const PREFIX = 'statut: ';

async function connection(github, query, variables, select) {
  const nodes = [];
  let after = null;
  do {
    const page = select(await github.graphql(query, {...variables, after}));
    nodes.push(...page.nodes);
    if (!page.pageInfo.hasNextPage) break;
    after = page.pageInfo.endCursor;
  } while (after);
  return nodes;
}

const PR_ISSUES = `query($owner: String!, $repo: String!, $number: Int!, $after: String) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      closingIssuesReferences(first: 100, after: $after) {
        nodes { number repository { nameWithOwner } }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}`;

const ISSUE_PRS = `query($owner: String!, $repo: String!, $number: Int!, $after: String) {
  repository(owner: $owner, name: $repo) {
    issue(number: $number) {
      closedByPullRequestsReferences(first: 100, after: $after, includeClosedPrs: true) {
        nodes { state }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}`;

function desiredStatus(issue, labels, pulls) {
  if (issue.state === 'closed') return null;
  if (labels.includes(`${PREFIX}bloqué`)) return `${PREFIX}bloqué`;
  if (pulls.some(pr => pr.state === 'OPEN')) return `${PREFIX}en cours`;
  if (pulls.some(pr => pr.state === 'MERGED')) return `${PREFIX}à valider`;
  return `${PREFIX}à faire`;
}

async function sync({github, context, core, dryRun = false}) {
  const {owner, repo} = context.repo;
  let numbers;
  if (context.eventName === 'issues') {
    numbers = [context.payload.issue.number];
  } else {
    const number = Number(context.payload.pull_request?.number ?? context.payload.inputs?.pr_number);
    if (!Number.isSafeInteger(number) || number <= 0) throw new Error('Numéro de PR invalide');
    const issues = await connection(github, PR_ISSUES, {owner, repo, number},
      data => data.repository.pullRequest.closingIssuesReferences);
    // Ne jamais écrire dans un autre dépôt, même si la PR le référence.
    numbers = issues.filter(issue =>
      issue.repository.nameWithOwner.toLowerCase() === `${owner}/${repo}`.toLowerCase()
    ).map(issue => issue.number);
  }

  for (const number of new Set(numbers)) {
    const params = {owner, repo, issue_number: number};
    // Relire l'état courant : un ancien événement peut s'exécuter après une fusion.
    const {data: issue} = await github.rest.issues.get(params);
    const labels = (await github.paginate(github.rest.issues.listLabelsOnIssue,
      {...params, per_page: 100})).map(label => label.name);
    const pulls = issue.state === 'closed' ? [] : await connection(
      github, ISSUE_PRS, {owner, repo, number},
      data => data.repository.issue.closedByPullRequestsReferences);
    const target = desiredStatus(issue, labels, pulls);
    core.info(`#${number} → ${target ?? 'fermée, sans statut'}`);
    if (dryRun) continue;

    // Ajouter avant de retirer : un label manquant ne doit pas effacer le statut actuel.
    if (target && !labels.includes(target)) {
      await github.rest.issues.addLabels({...params, labels: [target]});
    }
    for (const name of labels.filter(label => label.startsWith(PREFIX) && label !== target)) {
      try {
        await github.rest.issues.removeLabel({...params, name});
      } catch (error) {
        // Un utilisateur peut avoir retiré ce label depuis la lecture précédente.
        if (error.status !== 404) throw error;
      }
    }
  }
}

module.exports = sync;
module.exports.desiredStatus = desiredStatus;
