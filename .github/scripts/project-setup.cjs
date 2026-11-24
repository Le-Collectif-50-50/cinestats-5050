// Configuration reproductible du suivi ; l'import historique est borné au 24/11/2026.
const {execFileSync} = require('node:child_process');
const {cliGithub, STATUSES} = require('./project-sync.cjs');
const config = require('../projects.json');

const MILESTONES = {
  collecte: 'Collecte et orchestration opérationnelles',
  publication: 'Publication dbt fiabilisée',
  qualification: 'Qualification des données',
  migration: 'Migration et déploiement',
  securite: 'Accès et sécurité',
  supervision: 'Supervision et reprise'
};
// Les numéros sont propres au dépôt, jamais interprétés hors de celui-ci.
const SEEDS = {
  'cinestats-5050': {
    collecte: [15, 17, 18, 22, 30, 35, 50, 54, 61, 62, 83, 84, 88, 89, 92],
    publication: [4, 23, 25, 31, 32, 33, 34, 37, 38, 39, 41, 42, 43, 45, 56, 57, 58, 59, 60, 77, 82, 85, 86, 87, 90, 91, 95],
    qualification: [24, 44, 46, 47, 48, 49, 51, 52, 53, 55, 63, 64, 65, 66, 67, 68, 69, 70, 73, 75, 76, 78, 79, 80, 81, 94],
    migration: [1, 2, 7, 8, 11],
    securite: [3, 6, 9, 12, 13, 14, 16, 19, 36],
    supervision: [10, 71, 72],
    shared: [11, 12, 16, 35, 71, 72]
  },
  'cinestats-infra': {
    securite: [2, 4, 5, 6, 7, 8, 9, 10],
    supervision: [1, 3, 11],
    shared: [4]
  }
};

function rest(endpoint, method = 'GET', body) {
  const args = ['api', endpoint, '--method', method];
  if (body) args.push('--input', '-');
  return JSON.parse(execFileSync('gh', args, {encoding: 'utf8',
    input: body ? JSON.stringify(body) : undefined, maxBuffer: 16 * 1024 * 1024,
    stdio: ['pipe', 'pipe', 'pipe']}));
}

function restPages(endpoint) {
  const all = [];
  for (let page = 1; ; page++) {
    const items = rest(`${endpoint}${endpoint.includes('?') ? '&' : '?'}per_page=100&page=${page}`);
    all.push(...items);
    if (items.length < 100) return all;
  }
}

async function setup({apply = false} = {}) {
  const github = cliGithub();
  const read = () => github.graphql(`query($owner: String!) {
    organization(login: $owner) { id projectsV2(first: 100) { nodes { id number title closed items { totalCount } } } }
  }`, {owner: config.owner}).organization;
  const org = read();
  if (org.projectsV2.nodes.length === 100) throw new Error('Plus de 100 Projects : paginer avant toute modification');
  const unused = org.projectsV2.nodes.filter(p => !p.closed && p.items.totalCount === 0 && p.title === "@ndretex's untitled project")
    .sort((a, b) => a.number - b.number);
  const projects = [];
  for (const spec of config.projects) {
    const matches = org.projectsV2.nodes.filter(p => !p.closed && p.title === spec.title);
    if (matches.length > 1) throw new Error(`Projets homonymes : ${spec.title}`);
    let project = matches[0] ?? unused.shift();
    console.log(`${apply ? '' : '[simulation] '}${project ? 'Configurer' : 'Créer'} ${spec.title}`);
    if (!apply) continue;
    if (!project) project = github.graphql(`mutation($owner: ID!, $title: String!) {
      createProjectV2(input: {ownerId: $owner, title: $title}) { projectV2 { id number } }
    }`, {owner: org.id, title: spec.title}).createProjectV2.projectV2;
    github.graphql(`mutation($id: ID!, $title: String!, $readme: String!) {
      updateProjectV2(input: {projectId: $id, title: $title, public: true, readme: $readme}) { projectV2 { id } }
    }`, {id: project.id, title: spec.title,
      readme: `Suivi transverse des dépôts cinestats-5050 et cinestats-infra.\n\nLabel de routage : \`${spec.label}\`. Les labels statut des issues pilotent Status ; les clôtures et fusions alimentent l’historique. Une fusion ne prouve ni le déploiement ni la validation métier.\n\n[Documentation et contribution](https://github.com/${config.owner}/cinestats-5050/wiki).`});
    for (const repo of config.repositories) {
      const repositoryId = github.graphql(`query($owner: String!, $repo: String!) {
        repository(owner: $owner, name: $repo) { id }
      }`, {owner: config.owner, repo}).repository.id;
      github.graphql(`mutation($project: ID!, $repo: ID!) {
        linkProjectV2ToRepository(input: {projectId: $project, repositoryId: $repo}) { repository { id } }
      }`, {project: project.id, repo: repositoryId});
    }
    const details = github.graphql(`query($id: ID!) { node(id: $id) { ... on ProjectV2 {
      fields(first: 100) { nodes { ... on ProjectV2Field { id name }
        ... on ProjectV2SingleSelectField { id name options { id name } } } }
      views(first: 100) { nodes { id name } }
    } } }`, {id: project.id}).node;
    const status = details.fields.nodes.find(f => f.name === 'Status');
    if (!status) throw new Error('Champ Status absent');
    const colors = ['GRAY', 'YELLOW', 'BLUE', 'RED', 'GREEN', 'PURPLE'];
    // Conserver les autres options/champs d'un projet réutilisé.
    const options = STATUSES.map((name, i) => ({
      ...(status.options.find(o => o.name === name)?.id ? {id: status.options.find(o => o.name === name).id} : {}),
      name, color: colors[i], description: ''
    }));
    for (const extra of status.options.filter(o => !STATUSES.includes(o.name) && project.title !== "@ndretex's untitled project")) {
      options.push({id: extra.id, name: extra.name, color: 'GRAY', description: ''});
    }
    github.graphql(`mutation($id: ID!, $options: [ProjectV2SingleSelectFieldOptionInput!]) {
      updateProjectV2Field(input: {fieldId: $id, singleSelectOptions: $options}) { projectV2Field { ... on ProjectV2SingleSelectField { id } } }
    }`, {id: status.id, options});
    const visible = ['Title', 'Status', 'Repository', 'Labels', 'Assignees', 'Milestone'];
    const visibleFieldIds = visible.map(name => details.fields.nodes.find(f => f.name === name)?.id).filter(Boolean);
    const views = [
      ['Pilotage', 'BOARD_LAYOUT', 'is:open'],
      ['À valider et blocages', 'TABLE_LAYOUT', 'is:issue is:open status:"À valider","Bloqué"'],
      ['PR à relire', 'TABLE_LAYOUT', 'is:pr is:open'],
      ['Livraisons', 'TABLE_LAYOUT', ''],
      ['Historique', 'TABLE_LAYOUT', 'is:closed']
    ];
    for (const [name, layout, filter] of views) {
      let view = details.views.nodes.find(v => v.name === name);
      // Réutiliser la vue initiale uniquement sur les projets initialement vides et sans titre.
      if (!view && name === 'Pilotage' && project.title === "@ndretex's untitled project") {
        view = details.views.nodes[0];
      }
      if (!view) view = github.graphql(`mutation($project: ID!, $name: String!, $layout: ProjectV2ViewLayout!, $configuration: ProjectV2ViewConfigurationInput) {
        createProjectV2View(input: {projectId: $project, name: $name, layout: $layout, configuration: $configuration}) { projectV2View { id } }
      }`, {project: project.id, name, layout, configuration: {visibleFieldIds}}).createProjectV2View.projectV2View;
      github.graphql(`mutation($id: ID!, $name: String!, $layout: ProjectV2ViewLayout!, $filter: String!, $configuration: ProjectV2ViewConfigurationInput) {
        updateProjectV2View(input: {viewId: $id, name: $name, layout: $layout, filter: $filter, configuration: $configuration}) { projectV2View { id } }
      }`, {id: view.id, name, layout, filter, configuration: {visibleFieldIds: name === 'PR à relire'
        ? [...visibleFieldIds, ...details.fields.nodes.filter(f => f.name === 'Reviewers').map(f => f.id)] : visibleFieldIds}});
    }
    projects.push({title: spec.title, number: project.number});
  }

  for (const repo of config.repositories) {
    const prefix = `repos/${config.owner}/${repo}`;
    const seeds = SEEDS[repo];
    const labels = restPages(`${prefix}/labels`);
    for (const spec of config.projects) {
      if (labels.some(label => label.name === spec.label)) continue;
      console.log(`${apply ? '' : '[simulation] '}Label ${repo} : ${spec.label}`);
      if (apply) rest(`${prefix}/labels`, 'POST', {name: spec.label, color: spec.label.endsWith('ingestion') ? '0E8A16' : '1D76DB',
        description: 'Routage vers le Project transverse correspondant'});
    }
    const milestones = restPages(`${prefix}/milestones?state=all`);
    const source = restPages(`${prefix}/issues?state=all`);
    const assigned = new Set();
    for (const [key, numbers] of Object.entries(seeds)) {
      if (key === 'shared') continue;
      let milestone = milestones.find(m => m.title === MILESTONES[key]);
      if (!milestone && numbers.length) {
        console.log(`${apply ? '' : '[simulation] '}Milestone ${repo} : ${MILESTONES[key]}`);
        if (apply) milestone = rest(`${prefix}/milestones`, 'POST', {title: MILESTONES[key],
          description: `Livrable : ${MILESTONES[key]}. Les clôtures GitHub ne prouvent pas le déploiement ni la validation métier.`});
      }
      for (const number of numbers) {
        if (assigned.has(number)) throw new Error(`Milestone historique ambigu : ${repo}#${number}`);
        assigned.add(number);
        const item = source.find(item => item.number === number);
        if (!item) throw new Error(`Élément historique absent : ${repo}#${number}`);
        const infrastructure = ['migration', 'securite', 'supervision'].includes(key);
        const routes = seeds.shared.includes(number) ? config.projects : [config.projects[infrastructure ? 1 : 0]];
        const missing = routes.filter(route => !item.labels.some(label => label.name === route.label)).map(route => route.label);
        console.log(`${apply ? '' : '[simulation] '}${repo}#${number} → ${routes.map(r => r.label).join(', ')} ; ${MILESTONES[key]}`);
        if (!apply) continue;
        if (missing.length) rest(`${prefix}/issues/${number}/labels`, 'POST', {labels: missing});
        // Ne pas écraser une attribution de milestone faite après l'import initial.
        if (!item.milestone) rest(`${prefix}/issues/${number}`, 'PATCH', {milestone: milestone.number});
      }
    }
  }
  if (apply) console.log(JSON.stringify(projects));
}

module.exports = {setup, SEEDS, MILESTONES};
if (require.main === module) {
  const args = process.argv.slice(2);
  if (args.some(arg => !['--apply', '--dry-run'].includes(arg)) || args.length > 1) {
    console.error('Usage : node .github/scripts/project-setup.cjs [--dry-run|--apply]');
    process.exitCode = 1;
  } else setup({apply: args.includes('--apply')}).catch(error => {
    console.error(error.message); process.exitCode = 1;
  });
}
