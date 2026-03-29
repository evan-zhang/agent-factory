/**
 * Skill: report-prepare
 * 准备汇报内容供用户确认（不调用 API，仅格式化输出）
 *
 * 流程：[生成草稿 draftGen] → [展示内容给用户] → [用户确认] → [调用 reportSubmit 正式发送]
 */

import type { ReportPrepareInput, ReportPrepareOutput } from '../shared/types.js';

/** 将 HTML 内容转为纯文本预览（截取前200字） */
function htmlToPreview(html: string, maxLen = 200): string {
  const text = html.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
  if (text.length <= maxLen) return text;
  return text.slice(0, maxLen) + '...';
}

/** 格式化文件列表摘要 */
function formatAttachmentSummary(filePaths?: string[], fileNames?: string[]): string {
  if (!filePaths || filePaths.length === 0) return '无附件';
  return filePaths.map((name, i) => `  ${i + 1}. ${fileNames?.[i] ?? name}`).join('\n');
}

export async function reportPrepare(input: ReportPrepareInput): Promise<ReportPrepareOutput> {
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

  const previewText = htmlToPreview(contentHtml);
  const attachmentSummary = formatAttachmentSummary(filePaths, fileNames);
  const attachmentCount = filePaths?.length ?? 0;

  // 组装展示给用户的完整确认信息
  const confirmInfo = {
    main: main.trim(),
    contentHtml,
    contentType,
    typeId,
    grade,
    acceptEmpIdList: acceptEmpIdList ?? [],
    copyEmpIdList: copyEmpIdList ?? [],
    reportLevelList: reportLevelList ?? [],
    previewText,
    attachmentSummary,
    attachmentCount,
    confirmPrompt: `【汇报确认】

标题：${main.trim()}

正文预览：
${previewText}

附件（${attachmentCount}个）：
${attachmentSummary}

---
以上为将发送的完整汇报内容，请回复"确认发送"后我将正式提交。`,
  };

  return { success: true, data: { confirmInfo } };
}
