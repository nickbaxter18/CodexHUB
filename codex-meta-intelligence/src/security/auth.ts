import crypto from 'node:crypto';

interface JwtPayload {
  sub: string;
  aud: string;
  exp: number;
  [key: string]: unknown;
}

const base64UrlEncode = (input: Buffer): string => input.toString('base64url');

const sign = (data: string, secret: string): string => {
  return crypto.createHmac('sha256', secret).update(data).digest('base64url');
};

export const createJwt = (payload: JwtPayload, secret: string): string => {
  const header = base64UrlEncode(Buffer.from(JSON.stringify({ alg: 'HS256', typ: 'JWT' })));
  const body = base64UrlEncode(Buffer.from(JSON.stringify(payload)));
  const signature = sign(`${header}.${body}`, secret);
  return `${header}.${body}.${signature}`;
};

export const verifyJwt = (token: string, secret: string): JwtPayload | undefined => {
  const [headerB64, payloadB64, signature] = token.split('.');
  if (!headerB64 || !payloadB64 || !signature) return undefined;
  const expectedSignature = sign(`${headerB64}.${payloadB64}`, secret);
  if (expectedSignature !== signature) return undefined;
  const payload = JSON.parse(Buffer.from(payloadB64, 'base64url').toString('utf8')) as JwtPayload;
  if (payload.exp < Math.floor(Date.now() / 1000)) {
    return undefined;
  }
  return payload;
};
