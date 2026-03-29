/**
 * Skill: ai-report-chat
 * 对指定汇报集合进行 AI 问答（SSE 流式）
 */

import { cworkClient } from '../shared/cwork-client.js';
import type { AiReportChatInput, AiReportChatOutput } from '../shared/types.js';

export async function aiReportChat(
  input: AiReportChatInput
): Promise<AiReportChatOutput> {
  const { reportIdList, userContent, aiType = 42 } = input;

  if (!reportIdList || reportIdList.length === 0) {
    return { success: false, message: 'reportIdList 不能为空' };
  }
  if (!userContent?.trim()) {
    return { success: false, message: 'userContent 不能为空' };
  }

  try {
    // SSE 流式调用，返回可读流
    const stream = await cworkClient.aiSseQa(userContent.trim(), reportIdList, aiType);
    return {
      success: true,
      data: {
        stream,
        reportCount: reportIdList.length,
        message: 'SSE 流式响应，请消费 stream 对象获取逐块内容',
      },
    };
  } catch (error) {
    return {
      success: false,
      message: `AI 问答失败: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}
