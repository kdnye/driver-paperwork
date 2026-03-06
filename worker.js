const MOUNT_PATH = process.env.MOUNT_PATH || '/driver_paperwork';

const renamerOptions = {
  provider: 'ollama',
  model: 'llava',
  baseURL: process.env.OLLAMA_BASE_URL || 'http://127.0.0.1:11434',
  logisticsMode: true,
  inputPath: MOUNT_PATH,
};

module.exports = {
  renamerOptions,
};
