'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import styles from './editor.module.css';

type Box = [number, number, number, number];
type Gender = 'female' | 'male' | 'unknown' | null;
type Face = { id: string; bbox: Box; gender: Gender; age_range: string | null; detection_confidence?: number | null };
type Annotation = Face & { source_prediction_id: string | null; deleted: boolean; reviewed: { bbox: boolean; gender: boolean; age_range: boolean }; note: string };
type Review = { revision: number; image_sha256: string; annotator: string; status: 'draft' | 'validated'; complete: boolean; annotations: Annotation[]; updated_at: string | null };
type Poster = { id: string; title: string; status: string; allocine_id: number | null };
type Detail = { manifest: { id: string; title: string; width: number; height: number; prediction_stage: string; run_id: string | null; code_version: string | null }; predictions: Face[]; review: Review };
const ages = ['0-2', '3-9', '10-19', '20-29', '30-39', '40-49', '50-59', '60-69', '70+', 'unknown'];
const genders = { female: 'Féminin perçu', male: 'Masculin perçu', unknown: 'Indéterminable' };
const api = '/api/annotation';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${api}${path}`, { ...init, cache: 'no-store', headers: { 'Content-Type': 'application/json' } });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(typeof body.detail === 'string' ? body.detail : 'Requête refusée. Vérifier les champs.');
  }
  return response.json();
}

export default function PosterEditor() {
  const [posters, setPosters] = useState<Poster[]>([]);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [review, setReview] = useState<Review | null>(null);
  const [selected, setSelected] = useState('');
  const [allocine, setAllocine] = useState('');
  const [error, setError] = useState('');
  const [saveState, setSaveState] = useState('');
  const [busy, setBusy] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [mode, setMode] = useState<'select' | 'add' | 'pan'>('select');
  const [originals, setOriginals] = useState(false);
  const [past, setPast] = useState<Review[]>([]);
  const [future, setFuture] = useState<Review[]>([]);
  const [preview, setPreview] = useState<Box | null>(null);
  const svg = useRef<SVGSVGElement>(null);
  const viewport = useRef<HTMLDivElement>(null);
  const latest = useRef<Review | null>(null);
  const revision = useRef(0);
  const saving = useRef(false);
  const generation = useRef(0);
  const gesture = useRef<{ start: [number, number]; box?: Box; id?: string; resize?: boolean; scroll?: [number, number] } | null>(null);

  const refresh = useCallback(async () => setPosters(await request<Poster[]>('/posters')), []);
  useEffect(() => { refresh().catch(e => setError(e.message)); }, [refresh]);
  useEffect(() => {
    const warn = (e: BeforeUnloadEvent) => { if (dirty || saving.current) e.preventDefault(); };
    window.addEventListener('beforeunload', warn);
    return () => window.removeEventListener('beforeunload', warn);
  }, [dirty]);

  const open = async (id: string, discard = false) => {
    if (saving.current || (dirty && !discard)) { setError('Sauvegarder les modifications avant de changer d’affiche.'); return; }
    setBusy(true); setError('');
    try {
      const value = await request<Detail>(`/posters/${id}`);
      generation.current++;
      setDetail(value); setReview(value.review); latest.current = value.review; revision.current = value.review.revision;
      setSelected(value.review.annotations[0]?.id || ''); setPast([]); setFuture([]); setZoom(1); setDirty(false); setSaveState('Sauvegardé');
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  };

  const save = useCallback(async () => {
    if (!latest.current || !detail || saving.current) return;
    const snapshot = latest.current;
    const gen = generation.current;
    saving.current = true; setSaveState('Sauvegarde…');
    try {
      const saved = await request<Review>(`/posters/${detail.manifest.id}/review`, {
        method: 'PUT', body: JSON.stringify({ ...snapshot, revision: revision.current }),
      });
      if (generation.current !== gen) return;
      revision.current = saved.revision;
      if (latest.current === snapshot) {
        latest.current = saved; setReview(saved); setDirty(false); setSaveState('Sauvegardé');
      } else {
        setSaveState('Modifications en attente');
      }
      setError('');
      await refresh();
    } catch (e) { setError((e as Error).message); setSaveState('Échec de sauvegarde — réessayer ou recharger'); }
    finally { saving.current = false; }
  }, [detail, refresh]);

  useEffect(() => {
    if (!dirty || saveState.startsWith('Échec')) return;
    const timer = setTimeout(() => { void save(); }, 700);
    return () => clearTimeout(timer);
  }, [review, dirty, save, saveState]);

  const change = (next: Review, history = true) => {
    if (!review) return;
    if (history) { setPast(items => [...items.slice(-49), review]); setFuture([]); }
    const value = { ...next, status: 'draft' as const, complete: false };
    latest.current = value; setReview(value); setDirty(true); setSaveState('Modifications en attente');
  };
  const update = (id: string, patch: Partial<Annotation>) => {
    if (review) change({ ...review, annotations: review.annotations.map(a => a.id === id ? { ...a, ...patch } : a) });
  };
  const undo = (redo = false) => {
    if (!review) return;
    const stack = redo ? future : past;
    const next = stack[stack.length - 1];
    if (!next) return;
    if (redo) { setFuture(stack.slice(0, -1)); setPast([...past, review]); }
    else { setPast(stack.slice(0, -1)); setFuture([...future, review]); }
    change(next, false);
  };
  const point = (e: React.PointerEvent): [number, number] => {
    const matrix = svg.current?.getScreenCTM()?.inverse();
    const p = new DOMPoint(e.clientX, e.clientY).matrixTransform(matrix);
    return [Math.round(Math.max(0, Math.min(detail!.manifest.width, p.x))), Math.round(Math.max(0, Math.min(detail!.manifest.height, p.y)))];
  };
  const down = (e: React.PointerEvent, a?: Annotation, resize = false) => {
    if (!detail || !review || e.button !== 0) return;
    e.preventDefault(); e.stopPropagation();
    svg.current?.setPointerCapture(e.pointerId);
    if (mode === 'pan') {
      gesture.current = { start: [e.clientX, e.clientY], scroll: [viewport.current!.scrollLeft, viewport.current!.scrollTop] }; return;
    }
    const start = point(e);
    if (mode === 'add') { gesture.current = { start }; setPreview([start[0], start[1], start[0], start[1]]); }
    else if (a) { setSelected(a.id); gesture.current = { start, box: a.bbox, id: a.id, resize }; setPreview(a.bbox); }
  };
  const move = (e: React.PointerEvent) => {
    const g = gesture.current;
    if (!g || !detail) return;
    if (g.scroll) {
      viewport.current!.scrollLeft = g.scroll[0] - (e.clientX - g.start[0]);
      viewport.current!.scrollTop = g.scroll[1] - (e.clientY - g.start[1]); return;
    }
    const [x, y] = point(e);
    if (!g.box) setPreview([Math.min(x, g.start[0]), Math.min(y, g.start[1]), Math.max(x, g.start[0]), Math.max(y, g.start[1])]);
    else if (g.resize) setPreview([g.box[0], g.box[1], Math.max(g.box[0] + 1, x), Math.max(g.box[1] + 1, y)]);
    else {
      const dx = Math.max(-g.box[0], Math.min(detail.manifest.width - g.box[2], x - g.start[0]));
      const dy = Math.max(-g.box[1], Math.min(detail.manifest.height - g.box[3], y - g.start[1]));
      setPreview([g.box[0] + dx, g.box[1] + dy, g.box[2] + dx, g.box[3] + dy]);
    }
  };
  const up = () => {
    const g = gesture.current; gesture.current = null;
    if (g && preview && review && preview[2] > preview[0] && preview[3] > preview[1]) {
      if (g.id) {
        const a = review.annotations.find(a => a.id === g.id)!;
        if (JSON.stringify(a.bbox) !== JSON.stringify(preview)) update(g.id, { bbox: preview, reviewed: { ...a.reviewed, bbox: true } });
      } else if (!g.scroll) {
        const id = `manual-${crypto.randomUUID()}`;
        change({ ...review, annotations: [...review.annotations, { id, bbox: preview, gender: null, age_range: null, source_prediction_id: null, deleted: false, reviewed: { bbox: true, gender: false, age_range: false }, note: '' }] });
        setSelected(id); setMode('select');
      }
    }
    setPreview(null);
  };
  const importFilm = async () => {
    if (dirty || saving.current) { setError('Sauvegarder avant d’importer une autre affiche.'); return; }
    setBusy(true); setError('');
    try {
      const value = await request<{ id: string }>(`/import/allocine/${allocine}`, { method: 'POST' });
      await refresh(); await open(value.id);
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  };
  const face = review?.annotations.find(a => a.id === selected);
  const ready = review?.annotations.every(a => a.deleted || (a.gender !== null && a.age_range !== null && Object.values(a.reviewed).every(Boolean)));

  return <main className={styles.editor}>
    <header><p className={styles.eyebrow}>ML IMAGE · JEU DE RÉFÉRENCE</p><h1>Annoter une affiche</h1><p>Relire les visages, le genre perçu et la tranche d’âge apparente.</p></header>
    <section className={styles.toolbar} aria-label="Choisir une affiche">
      <label>Identifiant Allociné<input value={allocine} onChange={e => setAllocine(e.target.value)} inputMode="numeric" placeholder="259157" /></label>
      <button disabled={busy || !/^\d+$/.test(allocine)} onClick={importFilm}>Rechercher en base</button>
      <label>Affiches locales<select value={detail?.manifest.id || ''} disabled={busy} onChange={e => { if (e.target.value) void open(e.target.value); }}><option value="">Choisir une affiche</option>{posters.map(p => <option key={p.id} value={p.id}>{p.title} — {p.status === 'validated' ? 'validée' : 'brouillon'}</option>)}</select></label>
    </section>
    {error && <div role="alert" className={styles.error}>{error}</div>}
    {!detail && <p>Choisir une affiche locale ou saisir son identifiant Allociné. La recherche nécessite une connexion à la base configurée côté serveur.</p>}
    {detail && review && <>
      <div className={styles.heading}><h2>{detail.manifest.title}</h2><span role="status">{saveState} · {review.status === 'validated' ? 'Validée' : 'Brouillon'}</span></div>
      <p className={styles.meta}>Exécution : {detail.manifest.run_id || 'non renseignée'} · Code : {detail.manifest.code_version || 'non renseigné'}</p>
      {detail.manifest.prediction_stage === 'none' ? <p className={styles.notice}>Aucune prédiction préparée. Ajouter les visages manuellement ou préparer un nouveau dossier avec les résultats ML.</p> : <p className={styles.notice}>Prédictions déjà filtrées. Genre et âge hérités du personnage associé dans la bande-annonce. Vérifier aussi les visages manqués.</p>}
      <div className={styles.toolbar}>
        <button aria-pressed={mode === 'select'} onClick={() => setMode('select')}>Sélectionner / déplacer</button><button aria-pressed={mode === 'add'} onClick={() => setMode('add')}>Ajouter un visage</button><button aria-pressed={mode === 'pan'} onClick={() => setMode('pan')}>Déplacer l’image</button>
        <label>Zoom<input aria-label="Zoom" type="range" min="0.5" max="4" step="0.25" value={zoom} onChange={e => setZoom(Number(e.target.value))} /></label>
        <button disabled={!past.length} onClick={() => undo()}>Annuler</button><button disabled={!future.length} onClick={() => undo(true)}>Rétablir</button>
        <label><input type="checkbox" checked={originals} onChange={e => setOriginals(e.target.checked)} /> Prédictions originales (pointillés)</label>
      </div>
      <div className={styles.workspace}>
        <div ref={viewport} className={styles.viewport}>
          <svg ref={svg} aria-label="Affiche et boîtes des visages" viewBox={`0 0 ${detail.manifest.width} ${detail.manifest.height}`} style={{ width: `${zoom * 100}%`, minWidth: `${zoom * 100}%`, touchAction: 'none' }} onPointerDown={e => down(e)} onPointerMove={move} onPointerUp={up} onPointerCancel={() => { gesture.current = null; setPreview(null); }}>
            <image href={`${api}/posters/${detail.manifest.id}/image`} width={detail.manifest.width} height={detail.manifest.height} />
            {originals && detail.predictions.map(a => <rect key={a.id} x={a.bbox[0]} y={a.bbox[1]} width={a.bbox[2] - a.bbox[0]} height={a.bbox[3] - a.bbox[1]} fill="none" stroke="white" strokeWidth="2" strokeDasharray="5 4" pointerEvents="none" vectorEffect="non-scaling-stroke" />)}
            {review.annotations.map((a, index) => a.deleted ? null : <g key={a.id} onPointerDown={e => down(e, a)}>
              <rect x={a.bbox[0]} y={a.bbox[1]} width={a.bbox[2] - a.bbox[0]} height={a.bbox[3] - a.bbox[1]} fill={a.id === selected ? '#00d4aa22' : 'transparent'} stroke={a.id === selected ? '#00ffd0' : '#ffcf66'} strokeWidth="2" vectorEffect="non-scaling-stroke" />
              <text x={a.bbox[0]} y={Math.max(12, a.bbox[1] - 4)} fill="white" stroke="black" strokeWidth="0.5" paintOrder="stroke" fontSize={Math.max(10, detail.manifest.width / 65)}>{index + 1} · {a.gender ? genders[a.gender] : '?'} · {a.age_range || '?'}</text>
              {a.id === selected && <rect aria-label="Redimensionner le visage" x={a.bbox[2] - 5} y={a.bbox[3] - 5} width="10" height="10" fill="#00ffd0" onPointerDown={e => down(e, a, true)} />}
            </g>)}
            {preview && <rect x={preview[0]} y={preview[1]} width={preview[2] - preview[0]} height={preview[3] - preview[1]} fill="none" stroke="#00ffd0" strokeWidth="2" strokeDasharray="4 3" pointerEvents="none" vectorEffect="non-scaling-stroke" />}
          </svg>
        </div>
        <aside className={styles.panel}>
          <h3>Visages ({review.annotations.filter(a => !a.deleted).length})</h3>
          <div className={styles.faces}>{review.annotations.map((a, i) => <button key={a.id} aria-pressed={selected === a.id} onClick={() => setSelected(a.id)}>#{i + 1} {a.deleted ? 'Supprimé' : Object.values(a.reviewed).every(Boolean) ? 'Relu' : 'À relire'} · {a.gender ? genders[a.gender] : '?'} · {a.age_range || '?'}</button>)}</div>
          {face && <div className={styles.fields}>
            <strong>{face.source_prediction_id ? `Prédiction ${face.source_prediction_id}` : 'Ajout manuel'}</strong>
            {face.source_prediction_id && <small>Confiance de détection : {detail.predictions.find(p => p.id === face.source_prediction_id)?.detection_confidence?.toFixed(2) ?? 'non disponible'}. Confiances genre/âge : non disponibles.</small>}
            <button onClick={() => update(face.id, { deleted: !face.deleted })}>{face.deleted ? 'Restaurer ce visage' : 'Supprimer cette détection'}</button>
            {!face.deleted && <>
              <div className={styles.coordinates}>{face.bbox.map((value, index) => <label key={index}>{['x1', 'y1', 'x2', 'y2'][index]}<input aria-label={['x1', 'y1', 'x2', 'y2'][index]} type="number" value={value} onChange={e => { const bbox = [...face.bbox] as Box; bbox[index] = Number(e.target.value); update(face.id, { bbox, reviewed: { ...face.reviewed, bbox: false } }); }} /></label>)}</div>
              <label><input type="checkbox" checked={face.reviewed.bbox} onChange={e => update(face.id, { reviewed: { ...face.reviewed, bbox: e.target.checked } })} /> Boîte relue</label>
              <label>Genre perçu<select aria-label="Genre perçu" value={face.gender || ''} onChange={e => update(face.id, { gender: e.target.value as Gender, reviewed: { ...face.reviewed, gender: true } })}><option value="" disabled>Non renseigné</option>{Object.entries(genders).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>
              <label><input type="checkbox" checked={face.reviewed.gender} onChange={e => update(face.id, { reviewed: { ...face.reviewed, gender: e.target.checked } })} /> Genre relu</label>
              <label>Tranche d’âge apparente<select aria-label="Tranche d’âge apparente" value={face.age_range || ''} onChange={e => update(face.id, { age_range: e.target.value, reviewed: { ...face.reviewed, age_range: true } })}><option value="" disabled>Non renseignée</option>{ages.map(age => <option key={age} value={age}>{age === 'unknown' ? 'Indéterminable' : age}</option>)}</select></label>
              <label><input type="checkbox" checked={face.reviewed.age_range} onChange={e => update(face.id, { reviewed: { ...face.reviewed, age_range: e.target.checked } })} /> Âge relu</label>
              <button disabled={face.gender === null || face.age_range === null} onClick={() => update(face.id, { reviewed: { bbox: true, gender: true, age_range: true } })}>Tout valider pour ce visage</button>
              <label>Note<textarea value={face.note} maxLength={2000} onChange={e => update(face.id, { note: e.target.value })} /></label>
            </>}
          </div>}
        </aside>
      </div>
      <section className={styles.validation}>
        <label>Annotateur<input value={review.annotator} maxLength={100} onChange={e => change({ ...review, annotator: e.target.value })} /></label>
        <button onClick={() => { setSaveState('Modifications en attente'); void save(); }} disabled={!dirty}>Sauvegarder</button>
        <button disabled={saveState === 'Sauvegarde…'} onClick={() => { if (window.confirm('Abandonner les modifications non sauvegardées et recharger ?')) void open(detail.manifest.id, true); }}>Recharger / abandonner</button>
        <label><input type="checkbox" checked={review.complete} onChange={e => { const value = { ...review, complete: e.target.checked, status: 'draft' as const }; latest.current = value; setReview(value); setDirty(true); setSaveState('Modifications en attente'); }} /> J’ai relu toute l’affiche et ajouté les visages manqués.</label>
        <button disabled={!ready || !review.complete || dirty || review.status === 'validated'} onClick={() => { const value = { ...review, status: 'validated' as const }; latest.current = value; setReview(value); setDirty(true); setSaveState('Modifications en attente'); }}>Valider l’affiche</button>
        {review.status === 'validated' && !dirty && <a href={`${api}/posters/${detail.manifest.id}/export`} download>Exporter la référence et le bilan</a>}
      </section>
    </>}
  </main>;
}
