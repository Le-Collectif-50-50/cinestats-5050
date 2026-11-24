const {test} = require('node:test');
const assert = require('node:assert/strict');
const sync = require('./project-sync.cjs');

function issue(overrides = {}) {
  return {__typename: 'Issue', id: 'issue-41', number: 41, url: 'https://example.org/issues/41',
    state: 'OPEN', stateReason: null, repository: {nameWithOwner: 'org/repo'},
    labels: {nodes: [{name: 'projet: ingestion'}, {name: 'statut: à valider'}]}, ...overrides};
}

test('statuts : blocage prioritaire, réouverture, clôture et abandon', () => {
  assert.equal(sync.desiredStatus(issue()), 'À valider');
  assert.equal(sync.desiredStatus(issue({labels: {nodes: [
    {name: 'statut: en cours'}, {name: 'statut: bloqué'}]}})), 'Bloqué');
  assert.equal(sync.desiredStatus(issue({state: 'CLOSED', stateReason: 'COMPLETED'})), 'Terminé');
  assert.equal(sync.desiredStatus(issue({state: 'CLOSED', stateReason: 'NOT_PLANNED'})), 'Abandonné');
  assert.equal(sync.desiredStatus(issue({state: 'CLOSED', stateReason: null})), 'Abandonné');
  assert.equal(sync.desiredStatus(issue({stateReason: 'REOPENED'})), 'À valider');
  assert.equal(sync.desiredStatus(issue({labels: {nodes: []}})), 'À faire');
  assert.equal(sync.desiredStatus(issue({labels: {nodes: [{name: 'statut: en cours'}]}})), 'En cours');
});

test('PR : brouillon ouvert, fusion et fermeture sans fusion', () => {
  const pr = issue({__typename: 'PullRequest', merged: false});
  assert.equal(sync.desiredStatus(pr), 'En cours');
  assert.equal(sync.desiredStatus({...pr, state: 'CLOSED'}), 'Abandonné');
  assert.equal(sync.desiredStatus({...pr, state: 'MERGED', merged: true}), 'Terminé');
});

function fixture({source = [issue()], members = [], options = sync.STATUSES} = {}) {
  const writes = [];
  const github = {graphql: async (query, variables) => {
    const page = nodes => ({nodes, pageInfo: {hasNextPage: false, endCursor: null}});
    if (query.startsWith('mutation')) {
      writes.push({query, variables});
      if (query.includes('addProjectV2ItemById')) {
        const member = {id: `member-${variables.content}`, content: {id: variables.content}};
        members.push(member);
        return {addProjectV2ItemById: {item: member}};
      }
      const member = members.find(member => member.id === variables.item);
      member.fieldValueByName = {name: variables.option};
      return {updateProjectV2ItemFieldValue: {projectV2Item: {id: variables.item}}};
    }
    if (query.includes('repository(owner:')) return {repository: {
      issues: page(source.filter(item => item.__typename === 'Issue')),
      pullRequests: page(source.filter(item => item.__typename === 'PullRequest'))
    }};
    if (query.includes('organization(login:')) return {organization: {projectsV2: page([
      {id: 'project-1', title: 'Ingestion', closed: false}
    ])}};
    if (query.includes('fields(first:')) return {node: {fields: page([
      {id: 'status', name: 'Status', options: options.map(name => ({id: name, name}))}
    ])}};
    return {node: {items: page(members)}};
  }};
  return {github, writes, members, core: {info() {}}, settings: {owner: 'org',
    repositories: ['repo'], projects: [{title: 'Ingestion', label: 'projet: ingestion'}]}};
}

test('import puis réconciliation sans doublon ni écriture répétée', async () => {
  const f = fixture();
  assert.deepEqual(await sync({...f, dryRun: false}), {added: 1, updated: 1, unchanged: 0});
  f.writes.length = 0;
  assert.deepEqual(await sync({...f, dryRun: false}), {added: 0, updated: 0, unchanged: 1});
  assert.equal(f.members.length, 1);
  assert.equal(f.writes.length, 0);
});

test('retrait du label : conserve et actualise la participation historique', async () => {
  const f = fixture({source: [issue({labels: {nodes: []}, state: 'CLOSED', stateReason: 'COMPLETED'})],
    members: [{id: 'member-41', content: {id: 'issue-41'}, fieldValueByName: {name: 'À valider'}}]});
  await sync({...f, dryRun: false});
  assert.equal(f.members.length, 1);
  assert.equal(f.members[0].fieldValueByName.name, 'Terminé');
  assert.equal(f.writes.length, 1);
});

test('simulation : lectures, aucune mutation', async () => {
  const f = fixture();
  assert.deepEqual(await sync(f), {added: 1, updated: 1, unchanged: 0});
  assert.equal(f.writes.length, 0);
  assert.equal(f.members.length, 0);
});

test('élément partagé : ajouté et synchronisé dans les deux Projects', async () => {
  const f = fixture({source: [issue({labels: {nodes: [
    {name: 'projet: ingestion'}, {name: 'projet: infrastructure'}]}})]});
  const graphql = f.github.graphql;
  f.github.graphql = async (query, variables) => query.includes('organization(login:')
    ? {organization: {projectsV2: {nodes: [
      {id: 'project-1', title: 'Ingestion', closed: false},
      {id: 'project-2', title: 'Infrastructure', closed: false}
    ], pageInfo: {hasNextPage: false}}}}
    : graphql(query, variables);
  f.settings.projects.push({title: 'Infrastructure', label: 'projet: infrastructure'});
  const result = await sync({...f, dryRun: false});
  assert.equal(result.added, 2);
  assert.equal(result.updated, 2);
  assert.deepEqual(f.writes.filter(w => w.query.includes('addProjectV2ItemById'))
    .map(w => w.variables.project), ['project-1', 'project-2']);
});

test('registre historique : une seule attribution de milestone par dépôt', () => {
  const {SEEDS} = require('./project-setup.cjs');
  for (const seed of Object.values(SEEDS)) {
    const numbers = Object.entries(seed).filter(([key]) => key !== 'shared').flatMap(([, value]) => value);
    assert.equal(new Set(numbers).size, numbers.length);
    assert.ok(seed.shared.every(number => numbers.includes(number)));
  }
});

test('hors périmètre, brouillons de Project et contenu inaccessible : préservés', async () => {
  const f = fixture({source: [issue({labels: {nodes: []}})],
    members: [{id: 'draft', content: {}}, {id: 'redacted', content: null}]});
  assert.deepEqual(await sync({...f, dryRun: false}), {added: 0, updated: 0, unchanged: 0});
  assert.equal(f.writes.length, 0);
});

test('champ Status incomplet : échec avant toute mutation', async () => {
  const f = fixture({options: ['À faire']});
  await assert.rejects(sync({...f, dryRun: false}), /six options/);
  assert.equal(f.writes.length, 0);
});

test('erreur API : échec visible', async () => {
  const f = fixture();
  f.github.graphql = async () => {throw new Error('Identifiants ou permissions invalides');};
  await assert.rejects(sync(f), /Identifiants ou permissions invalides/);
});

test('pagination : suit tous les curseurs', async () => {
  const cursors = [];
  const github = {graphql: async (_, {after}) => {
    cursors.push(after);
    return {nodes: after ? [2] : [1], pageInfo: {hasNextPage: !after, endCursor: 'next'}};
  }};
  assert.deepEqual(await sync.pages(github, '', {}, data => data), [1, 2]);
  assert.deepEqual(cursors, [null, 'next']);
});
