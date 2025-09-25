interface PullRequestUpdate {
  repository: string;
  number: number;
  body: string;
}

export const formatPullRequestUpdate = (
  repository: string,
  number: number,
  summary: string
): PullRequestUpdate => ({
  repository,
  number,
  body: summary,
});
