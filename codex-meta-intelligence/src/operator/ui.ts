export interface OperatorWidget {
  id: string;
  title: string;
  description: string;
}

export interface OperatorDashboardState {
  widgets: OperatorWidget[];
}

export const createDefaultDashboard = (): OperatorDashboardState => ({
  widgets: [
    {
      id: 'tasks',
      title: 'Task Overview',
      description: 'Displays queued, running and completed tasks.',
    },
    { id: 'qa', title: 'QA Findings', description: 'Summarises recent QA issues and severities.' },
  ],
});
