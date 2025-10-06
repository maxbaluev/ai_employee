'use server';

import { readFile } from 'node:fs/promises';
import path from 'node:path';

/**
 * Loads a Markdown file from the repository root as a UTF-8 string.
 * Throws a descriptive error when the file cannot be read so the
 * consumer can surface a helpful message in the UI.
 */
export async function loadMarkdown(relativePath: string): Promise<string> {
  const absolutePath = path.isAbsolute(relativePath)
    ? relativePath
    : path.join(process.cwd(), relativePath);

  try {
    return await readFile(absolutePath, 'utf8');
  } catch (error) {
    throw new Error(`Failed to load markdown file at ${absolutePath}: ${(error as Error).message}`);
  }
}
