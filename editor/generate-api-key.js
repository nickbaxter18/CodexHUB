#!/usr/bin/env node

/**
 * Generate a secure API key for CodexHUB Editor
 * Usage: node generate-api-key.js
 */

import crypto from 'crypto';

function generateSecureApiKey(length = 32) {
  // Generate a cryptographically secure random string
  const buffer = crypto.randomBytes(length);
  return buffer.toString('base64')
    .replace(/\+/g, '-')  // Replace + with -
    .replace(/\//g, '_')  // Replace / with _
    .replace(/=/g, '');   // Remove padding
}

function generateApiKey() {
  const apiKey = generateSecureApiKey(32);
  
  console.log('🔑 Generated secure API key for CodexHUB Editor:');
  console.log('');
  console.log(`CODEX_API_KEY=${apiKey}`);
  console.log('');
  console.log('📝 Instructions:');
  console.log('1. Copy the above line to your .env file in the project root');
  console.log('2. Make sure your .env file is in the same directory as package.json');
  console.log('3. Restart the editor server');
  console.log('');
  console.log('⚠️  Security Note:');
  console.log('- Keep this API key secure and private');
  console.log('- Do not commit it to version control');
  console.log('- Consider rotating it periodically');
}

// Run if called directly
generateApiKey();

export { generateSecureApiKey, generateApiKey };
