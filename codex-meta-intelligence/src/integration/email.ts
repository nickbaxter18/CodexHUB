interface EmailMessage {
  to: string;
  subject: string;
  body: string;
}

export const composeEmail = (to: string, subject: string, body: string): EmailMessage => ({
  to,
  subject,
  body,
});
