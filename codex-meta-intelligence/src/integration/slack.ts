interface SlackMessage {
  channel: string;
  text: string;
}

export const createSlackMessage = (channel: string, text: string): SlackMessage => ({
  channel,
  text,
});
