/**
 * Skill: report-submit-with-attachments
 * 一站式发送带有多附件的汇报
 * 自动处理文件上传（逐个上传，失败重试3次）+ 汇报提交
 */

import { cworkClient } from '../shared/cwork-client.js';
import type { ReportSubmitWithAttachmentsInput, ReportSubmitWithAttachmentsOutput } from '../shared/types.js';

const MAX_RETRIES = 3;

async function uploadWithRetry(file: File): Promise<string> {
  let lastError: Error | unknown;
  for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
    try {
      const { fileId } = await cworkClient.uploadFile(file);
      return fileId;
    } catch (error) {
      lastError = error;
      if (attempt < MAX_RETRIES) {
        await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
      }
    }
  }
  throw lastError ?? new Error('文件上传失败');
}

export async function reportSubmitWithAttachments(
  input: ReportSubmitWithAttachmentsInput
): Promise<ReportSubmitWithAttachmentsOutput> {
  const {
    main,
    contentHtml,
    contentType = 'html',
    typeId = 9999,
    grade = '一般',
    acceptEmpIdList,
    copyEmpIdList,
    reportLevelList,
    filePaths,
    fileNames,
  } = input;

  if (!main?.trim()) return { success: false, message: '汇报标题不能为空' };
  if (!contentHtml?.trim()) return { success: false, message: '汇报内容不能为空' };

  // 至少传一个文件时才处理附件
  if (filePaths && filePaths.length > 0) {
    if (filePaths.length !== fileNames.length) {
      return { success: false, message: 'filePaths 和 fileNames 数量必须一致' };
    }
    // 数量建议不超过10个
    if (filePaths.length > 10) {
      return { success: false, message: '附件数量建议不超过10个，超出请分批提交' };
    }
  }

  try {
    // 1. 逐个上传文件（失败重试最多3次）
    const fileVOList = [];
    if (filePaths && filePaths.length > 0) {
      for (let i = 0; i < filePaths.length; i++) {
        const filePath = filePaths[i];
        const fileName = fileNames[i];
        try {
          const file = new File([], fileName, { type: 'application/octet-stream' });
          // 通过 fetch 读取本地文件
          const response = await fetch(`file://${filePath}`);
          if (!response.ok) {
            return { success: false, message: `文件读取失败: ${filePath}` };
          }
          const blob = await response.blob();
          const realFile = new File([blob], fileName);
          const fileId = await uploadWithRetry(realFile);
          fileVOList.push({ fileId, name: fileName, type: 'file' as const });
        } catch (error) {
          return {
            success: false,
            message: `第 ${i + 1} 个文件 ${fileName} 上传失败: ${error instanceof Error ? error.message : String(error)}`,
          };
        }
      }
    }

    // 2. 提交汇报
    const result = await cworkClient.submitReport({
      main,
      contentHtml,
      contentType,
      typeId,
      grade,
      privacyLevel: '非涉密',
      acceptEmpIdList,
      copyEmpIdList,
      reportLevelList: reportLevelList && reportLevelList.length > 0 ? reportLevelList : undefined,
      fileVOList: fileVOList.length > 0 ? fileVOList : undefined,
    });

    return { success: true, data: { reportId: result.id, uploadedFiles: fileVOList.length } };
  } catch (error) {
    return { success: false, message: `汇报提交失败: ${error instanceof Error ? error.message : String(error)}` };
  }
}
