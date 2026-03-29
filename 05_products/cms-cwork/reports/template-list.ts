/**
 * Skill: template-list
 * 查询最近处理过的事项列表（用于创建任务时选关联事项）
 */

import { cworkClient } from '../shared/cwork-client.js';
import type { TemplateListInput, TemplateListOutput } from '../shared/types.js';

export async function templateList(input: TemplateListInput): Promise<TemplateListOutput> {
  const { beginTime, endTime, limit = 50 } = input;

  try {
    const result = await cworkClient.listTemplates(beginTime, endTime, limit);
    const templates = result.recentOperateTemplates ?? [];
    return {
      success: true,
      data: {
        total: templates.length,
        list: templates.map(t => ({
          templateId: String(t.templateId),
          main: t.main,
        })),
      },
    };
  } catch (error) {
    return {
      success: false,
      message: `事项列表查询失败: ${error instanceof Error ? error.message : String(error)}`,
    };
  }
}
