// Les labels existants restent la source de vérité. Aucune écriture dans les issues/PR.
const {execFileSync} = require('node:child_process');
const config = require('../projects.json');

const STATUSES = ['À faire', 'En cours', 'À valider', 'Bloqué', 'Terminé', 'Abandonné'];
const PAGE = 'pageInfo { hasNextPage endCursor }';
const CONTENT = `id number url state labels(first: 100) { nodes { name } }
  repository { nameWithOwner }`;

function desiredStatus(item) {
  if (item.__typename === 'PullRequest') {
    if (item.merged) return 'Terminé';
    return item.state === 'CLOSED' ? 'Abandonné' : 'En cours';
  }
  if (item.state === 'CLOSED') return item.stateReason === 'COMPLETED' ? 'Terminé' : 'Abandonné';
  const labels = item.labels.nodes.map(label => label.name);
  if (labels.includes('statut: bloqué')) return 'Bloqué';
  if (labels.includes('statut: en cours')) return 'En cours';
  if (labels.includes('statut: à valider')) return 'À valider';
  return 'À faire';
}

async function pages(github, query, variables, select) {
  const nodes = [];
  let after = null;
  do {
    const page = select(await github.graphql(query, {...variables, after}));
    nodes.push(...page.nodes.filter(Boolean));
    if (!page.pageInfo.hasNextPage) return nodes;
    after = page.pageInfo.endCursor;
  } while (after);
  throw new Error('Pagination GitHub incohérente : curseur absent');
}

async function sync({github, core, dryRun = true, settings = config}) {
  const source = new Map();
  for (const repo of settings.repositories) {
    for (const kind of ['issues', 'pullRequests']) {
      const detail = kind === 'issues' ? 'stateReason' : 'merged';
      const query = `query($owner: String!, $repo: String!, $after: String) {
        repository(owner: $owner, name: $repo) {
          ${kind}(first: 100, after: $after) {
            nodes { __typename ${CONTENT} ${detail} } ${PAGE}
          }
        }
      }`;
      const items = await pages(github, query, {owner: settings.owner, repo},
        data => data.repository[kind]);
      for (const item of items) source.set(item.id, item);
    }
  }

  const projects = await pages(github, `query($owner: String!, $after: String) {
    organization(login: $owner) { projectsV2(first: 100, after: $after) {
      nodes { id title closed } ${PAGE}
    } }
  }`, {owner: settings.owner}, data => data.organization.projectsV2);

  // Valider tous les champs avant la première écriture.
  const ready = [];
  for (const spec of settings.projects) {
    const matches = projects.filter(project => project.title === spec.title && !project.closed);
    if (matches.length !== 1) throw new Error(`Projet « ${spec.title} » : ${matches.length} correspondance(s), une attendue`);
    const project = matches[0];
    const fields = await pages(github, `query($id: ID!, $after: String) {
      node(id: $id) { ... on ProjectV2 { fields(first: 100, after: $after) {
        nodes { ... on ProjectV2SingleSelectField { id name options { id name } } } ${PAGE}
      } } }
    }`, {id: project.id}, data => data.node.fields);
    const field = fields.find(field => field.name === 'Status');
    if (!field || STATUSES.some(name => !field.options.some(option => option.name === name))) {
      throw new Error(`Projet « ${spec.title} » : configurer les six options du champ Status`);
    }
    const items = await pages(github, `query($id: ID!, $after: String) {
      node(id: $id) { ... on ProjectV2 { items(first: 100, after: $after) {
        nodes { id content { ... on Issue { id } ... on PullRequest { id } }
          fieldValueByName(name: "Status") { ... on ProjectV2ItemFieldSingleSelectValue { name } }
        } ${PAGE}
      } } }
    }`, {id: project.id}, data => data.node.items);
    const existing = new Map();
    for (const item of items) {
      if (!item.content?.id) continue;
      if (existing.has(item.content.id)) throw new Error(`Doublon dans « ${spec.title} » : ${item.content.id}`);
      existing.set(item.content.id, item);
    }
    ready.push({spec, project, field, existing});
  }

  const totals = {added: 0, updated: 0, unchanged: 0};
  for (const {spec, project, field, existing} of ready) {
    for (const item of source.values()) {
      let membership = existing.get(item.id);
      const routed = item.labels.nodes.some(label => label.name === spec.label);
      // Retirer un label ne supprime jamais l'historique du projet.
      if (!membership && !routed) continue;
      const status = desiredStatus(item);
      if (!membership) {
        core.info(`${dryRun ? '[simulation] ' : ''}Ajouter ${item.url} → ${spec.title}`);
        totals.added++;
        if (!dryRun) {
          const added = await github.graphql(`mutation($project: ID!, $content: ID!) {
            addProjectV2ItemById(input: {projectId: $project, contentId: $content}) { item { id } }
          }`, {project: project.id, content: item.id});
          membership = added.addProjectV2ItemById.item;
        }
      }
      if (membership?.fieldValueByName?.name === status) {
        totals.unchanged++;
        continue;
      }
      core.info(`${dryRun ? '[simulation] ' : ''}${item.url} → ${status} (${spec.title})`);
      totals.updated++;
      if (!dryRun) {
        await github.graphql(`mutation($project: ID!, $item: ID!, $field: ID!, $option: String!) {
          updateProjectV2ItemFieldValue(input: {projectId: $project, itemId: $item,
            fieldId: $field, value: {singleSelectOptionId: $option}}) { projectV2Item { id } }
        }`, {project: project.id, item: membership.id, field: field.id,
          option: field.options.find(option => option.name === status).id});
      }
    }
  }
  core.info(`${dryRun ? 'Simulation' : 'Synchronisation'} : ${JSON.stringify(totals)}`);
  return totals;
}

function cliGithub() {
  return {graphql(query, variables = {}) {
    const raw = execFileSync('gh', ['api', 'graphql', '--input', '-'], {
      input: JSON.stringify({query, variables}), encoding: 'utf8', maxBuffer: 16 * 1024 * 1024,
      stdio: ['pipe', 'pipe', 'pipe']
    });
    const result = JSON.parse(raw);
    if (result.errors) throw new Error(JSON.stringify(result.errors));
    return result.data;
  }};
}

module.exports = sync;
module.exports.desiredStatus = desiredStatus;
module.exports.pages = pages;
module.exports.cliGithub = cliGithub;
module.exports.STATUSES = STATUSES;

if (require.main === module) {
  const args = process.argv.slice(2);
  if (args.some(arg => !['--apply', '--dry-run'].includes(arg)) || args.length > 1) {
    console.error('Usage : node .github/scripts/project-sync.cjs [--dry-run|--apply]');
    process.exitCode = 1;
  } else {
    sync({github: cliGithub(), core: {info: console.log}, dryRun: !args.includes('--apply')})
      .catch(error => {console.error(error.message); process.exitCode = 1;});
  }
}
