const {test} = require('node:test');
const assert = require('node:assert/strict');
const sync = require('./issue-status.cjs');

test('transitions selon toutes les PR liées, avec priorité aux blocages manuels', () => {
  const status = (states, labels = [], state = 'open') =>
    sync.desiredStatus({state}, labels, states.map(state => ({state})));
  assert.equal(status(['OPEN']), 'statut: en cours');
  assert.equal(status(['MERGED']), 'statut: à valider');
  assert.equal(status(['CLOSED']), 'statut: à faire');
  assert.equal(status(['MERGED', 'OPEN']), 'statut: en cours');
  assert.equal(status(['OPEN'], ['statut: bloqué']), 'statut: bloqué');
  assert.equal(status(['MERGED'], ['statut: bloqué']), 'statut: bloqué');
  assert.equal(status(['OPEN'], ['statut: bloqué'], 'closed'), null);
});

function fixture({state = 'open', labels = ['bug', 'statut: à faire'],
  pulls = ['OPEN'], issues, paginateLinks = false} = {}) {
  const writes = [];
  const reads = [];
  const get = async args => {reads.push(args); return {data: {state}};};
  const listLabelsOnIssue = () => {};
  const github = {
    graphql: async (query, args) => {
      const isPR = query.includes('closingIssuesReferences(');
      const nodes = isPR ? (issues ?? [
        {number: 41, repository: {nameWithOwner: 'collectif/cinestats'}},
        {number: 42, repository: {nameWithOwner: 'autre/depot'}}
      ]) : pulls.map(state => ({state}));
      const page = {
        nodes: paginateLinks && !args.after ? [] : nodes,
        pageInfo: {hasNextPage: paginateLinks && !args.after, endCursor: 'next'}
      };
      return {repository: isPR ? {pullRequest: {closingIssuesReferences: page}} :
        {issue: {closedByPullRequestsReferences: page}}};
    },
    paginate: async () => labels.map(name => ({name})),
    rest: {issues: {
      get, listLabelsOnIssue,
      addLabels: async args => writes.push({add: args}),
      removeLabel: async args => writes.push({remove: args})
    }}
  };
  const context = {repo: {owner: 'collectif', repo: 'cinestats'},
    eventName: 'pull_request_target', payload: {pull_request: {number: 50}}};
  return {github, context, core: {info() {}}, writes, reads};
}

test('PR ouverte : ajoute en cours, retire ancien statut, préserve bug et autres dépôts', async () => {
  const f = fixture();
  await sync(f);
  assert.deepEqual(f.writes.map(w => w.add?.labels ?? w.remove.name),
    [['statut: en cours'], 'statut: à faire']);
  assert.deepEqual(f.reads.map(r => r.issue_number), [41]);
});

test('fusion : utilise les données courantes plutôt qu’un ancien événement ouvert', async () => {
  const f = fixture({pulls: ['MERGED']});
  await sync(f);
  assert.deepEqual(f.writes[0].add.labels, ['statut: à valider']);
});

test('issue fermée : retire tous les statuts sans rouvrir ni ajouter de label', async () => {
  const f = fixture({state: 'closed', labels: ['bug', 'statut: en cours', 'statut: bloqué']});
  f.context.eventName = 'issues';
  f.context.payload = {issue: {number: 41}};
  await sync(f);
  assert.deepEqual(f.writes.map(w => w.remove.name), ['statut: en cours', 'statut: bloqué']);
});

test('sans lien natif : aucun changement', async () => {
  const f = fixture({issues: []});
  await sync(f);
  assert.deepEqual(f.reads, []);
  assert.deepEqual(f.writes, []);
});

test('pagination des deux relations GraphQL', async () => {
  const f = fixture({paginateLinks: true});
  await sync(f);
  assert.deepEqual(f.writes[0].add.labels, ['statut: en cours']);
});

test('relance manuelle et idempotence', async () => {
  const f = fixture({labels: ['bug', 'statut: en cours']});
  f.context.eventName = 'workflow_dispatch';
  f.context.payload = {inputs: {pr_number: '50'}};
  await sync(f);
  assert.deepEqual(f.writes, []);
});

test('simulation sans écriture', async () => {
  const f = fixture();
  await sync({...f, dryRun: true});
  assert.deepEqual(f.writes, []);
  assert.equal(f.reads.length, 1);
});

test('erreur API de lecture : échec visible, aucun statut modifié', async () => {
  const f = fixture();
  f.github.graphql = async () => {throw new Error('API indisponible');};
  await assert.rejects(sync(f), /API indisponible/);
  assert.deepEqual(f.writes, []);
});
