interface SyncResult {
  syncedFiles: string[];
  conflicts: string[];
}

export const performSync = (localFiles: string[], remoteFiles: string[]): SyncResult => {
  const conflicts = localFiles.filter((file) => remoteFiles.includes(file));
  const uniqueLocal = localFiles.filter((file) => !conflicts.includes(file));
  const uniqueRemote = remoteFiles.filter((file) => !conflicts.includes(file));
  return {
    syncedFiles: [...uniqueLocal, ...uniqueRemote],
    conflicts,
  };
};
