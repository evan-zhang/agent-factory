/**
 * Skill: file-upload
 * 上传本地文件，获取 fileId
 */

import { cworkClient } from '../shared/cwork-client.js';
import type { FileUploadOutput } from '../shared/types.js';

export async function fileUpload(input: { file: File }): Promise<FileUploadOutput> {
  try {
    const { fileId } = await cworkClient.uploadFile(input.file);
    return { success: true, data: { fileId, fileName: input.file.name, fileSize: input.file.size } };
  } catch (error) {
    return { success: false, message: `文件上传失败: ${error instanceof Error ? error.message : String(error)}` };
  }
}
