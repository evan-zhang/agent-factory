/**
 * Skill: template-info-batch
 * 批量查询事项详情（根据 templateId 列表）
 */

import { cworkClient } from '../shared/cwork-client.js';
import type { TemplateInfoBatchInput, TemplateInfoBatchOutput } from '../shared/types.js';

export async function templateInfoBatch(
  input: TemplateInfoBatchInput
): Promise<TemplateInfoBatchOutput> {
  const { templateIds } = input;

  if (!templateIds || templateIds.length === 0) {
    return { success: false, message: 'templateIds 不能为空' };
  }

  try {
    const result = await cworkClient.listTemplatesByIds(templateIds);
    return {
      success: true,
      data: {
        total: result.length,
        list: result.map(t => ({
          templateId: String(t.templateId),
          main: t.main,
        })),
      },
    };
  } catch (error) {
    return {
      success: false,
      message: `事项详情查询失败: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}
