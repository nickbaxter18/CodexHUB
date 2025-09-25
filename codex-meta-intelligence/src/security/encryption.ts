import crypto from 'node:crypto';

const ALGORITHM = 'aes-256-gcm';

export const encrypt = (
  plainText: string,
  secret: string
): { iv: string; cipherText: string; authTag: string } => {
  const iv = crypto.randomBytes(12);
  const key = crypto.createHash('sha256').update(secret).digest();
  const cipher = crypto.createCipheriv(ALGORITHM, key, iv);
  const cipherText = Buffer.concat([cipher.update(plainText, 'utf8'), cipher.final()]);
  const authTag = cipher.getAuthTag();
  return {
    iv: iv.toString('hex'),
    cipherText: cipherText.toString('hex'),
    authTag: authTag.toString('hex'),
  };
};

export const decrypt = (
  payload: { iv: string; cipherText: string; authTag: string },
  secret: string
): string => {
  const key = crypto.createHash('sha256').update(secret).digest();
  const decipher = crypto.createDecipheriv(ALGORITHM, key, Buffer.from(payload.iv, 'hex'));
  decipher.setAuthTag(Buffer.from(payload.authTag, 'hex'));
  const decrypted = Buffer.concat([
    decipher.update(Buffer.from(payload.cipherText, 'hex')),
    decipher.final(),
  ]);
  return decrypted.toString('utf8');
};
