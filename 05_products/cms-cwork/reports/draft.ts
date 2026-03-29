/**
 * Skill: draft
 * 草稿箱管理：查询列表、查看详情、删除草稿
 *
 * 注意事项：
 * - delete 接口的 id 是草稿 ID（来自 list 返回的 id），不是 businessId
 * - detail 接口的 reportRecordId 是汇报 ID（来自 list 返回的 businessId，或 saveDraft 返回的 id）
 * - 5.28（草稿转正式发出）服务端未实现，本 Skill 不提供该功能
 */

import { cworkClient } from '../shared/cwork-client.js';
import type { SkillResult, DraftListItem, DraftDetail } from '../shared/types.js';

// -----------------------------------------------------------------------------
// 类型定义
// -----------------------------------------------------------------------------

export interface DraftListInput {
  pageIndex?: number;   // 默认 1
  pageSize?: number;    // 默认 20
}

export interface DraftListOutput extends SkillResult<{
  total: number;
  list: Array<{
    draftId: string;          // 删除时使用（5.27）
    reportRecordId: string;   // 查详情时使用（5.26）
    main?: string;
    createTime?: string;
    updateTime?: string;
  }>;
}> {}

export interface DraftDetailInput {
  reportRecordId: string;   // 汇报 ID（来自 list 的 businessId 或 saveDraft 返回的 id）
}

export interface DraftDetailOutput extends SkillResult<{
  id: string;
  main: string;
  contentHtml: string;
  contentType?: string;
  grade?: string;
  acceptEmployees: Array<{ empId: string; name: string; dept?: string }>;
  copyEmployees: Array<{ empId: string; name: string; dept?: string }>;
  reportLevelList: DraftDetail['reportLevelList'];
  files: Array<{ name: string; fileId?: string; type?: string }>;
  summary: string;   // 人类可读摘要，方便 Agent 直接呈现
}> {}

export interface DraftDeleteInput {
  draftId: string;   // 草稿 ID（来自 list 的 id，不是 businessId）
}

export interface DraftDeleteOutput extends SkillResult<{ deleted: boolean }> {}

// -----------------------------------------------------------------------------
// 实现
// -----------------------------------------------------------------------------

/** 列出草稿箱 */
export async function draftList(input: DraftListInput): Promise<DraftListOutput> {
  let { pageIndex = 1, pageSize = 20 } = input;
  if (pageIndex < 1) pageIndex = 1;
  if (pageSize < 1 || pageSize > 100) pageSize = 20;
  try {
    const result = await cworkClient.listDrafts({ pageIndex, pageSize });
    return {
      success: true,
      data: {
        total: result.total,
        list: result.list.map((item: DraftListItem) => ({
          draftId: String(item.id),
          reportRecordId: String(item.businessId),
          main: item.main,
          createTime: item.createTime,
          updateTime: item.updateTime,
        })),
      },
    };
  } catch (err) {
    return { success: false, message: String(err) };
  }
}

/** 查看草稿详情 */
export async function draftDetail(input: DraftDetailInput): Promise<DraftDetailOutput> {
  const { reportRecordId } = input;
  if (!reportRecordId) return { success: false, message: 'reportRecordId 不能为空' };
  try {
    const d = await cworkClient.getDraftDetail(reportRecordId);
    // acceptEmployeeList 在草稿状态下服务端返回 null；
    // 实际接收人在 reportLevelList[].empList 中（注意：文档写 levelUserList，服务端实际返回 empList）
    const levelList = d.reportLevelList ?? [];
    const allLevelUsers = levelList.flatMap(node => (node.empList ?? node.levelUserList ?? []) as Array<{ empId: string; name?: string }>);
    const acceptList = allLevelUsers.map(e => ({
      empId: String(e.empId), name: e.name ?? '', dept: undefined as string | undefined,
    }));
    const copyList = (d.copyEmployeeList ?? []).map(e => ({
      empId: String(e.empId), name: e.name, dept: e.mainDept,
    }));
    const files = (d.fileList ?? []).map(f => ({
      name: f.name, fileId: f.fileId, type: f.type,
    }));

    const acceptNames = acceptList.map(e => e.name).join('、') || '（无）';
    const copyNames = copyList.map(e => e.name).join('、') || '（无）';
    const fileNames = files.map(f => f.name).join('、') || '（无附件）';
    const summary = [
      `标题：${d.main}`,
      `接收人：${acceptNames}`,
      `抄送人：${copyNames}`,
      `附件：${fileNames}`,
      `正文预览：${(d.contentHtml ?? '').replace(/<[^>]+>/g, '').slice(0, 100)}...`,
    ].join('\n');

    return {
      success: true,
      data: {
        id: String(d.id),
        main: d.main,
        contentHtml: d.contentHtml,
        contentType: d.contentType,
        grade: d.grade,
        acceptEmployees: acceptList,
        copyEmployees: copyList,
        reportLevelList: d.reportLevelList ?? [],
        files,
        summary,
      },
    };
  } catch (err) {
    return { success: false, message: String(err) };
  }
}

/** 删除草稿（id = list 返回的 draftId） */
export async function draftDelete(input: DraftDeleteInput): Promise<DraftDeleteOutput> {
  const { draftId } = input;
  if (!draftId) return { success: false, message: 'draftId 不能为空' };
  try {
    const ok = await cworkClient.deleteDraft(draftId);
    if (!ok) {
      return { success: false, message: '删除草稿失败，后端返回 false（草稿可能已被删除或不存在）' };
    }
    return { success: true, data: { deleted: true } };
  } catch (err) {
    return { success: false, message: String(err) };
  }
}

// -----------------------------------------------------------------------------
// draftSave — 5.24 新增或更新汇报草稿
// -----------------------------------------------------------------------------

export interface DraftSaveInput {
  id?: string;              // 有值=更新草稿（全量覆盖），无值=新建草稿
  main: string;             // 标题（必填）
  contentHtml: string;      // 正文（必填）
  contentType?: string;     // 默认 markdown
  typeId?: number;          // 默认 9999
  grade?: string;           // 一般 | 紧急
  privacyLevel?: string;    // 非涉密 | 涉密
  planId?: string;
  templateId?: string;
  acceptEmpIdList?: string[];
  copyEmpIdList?: string[];
  reportLevelList?: import('../shared/types.js').DraftReportLevelParam[];
  fileVOList?: import('../shared/types.js').DraftFileVO[];
}

export interface DraftSaveOutput extends SkillResult<{ id: string }> {}

/**
 * 保存或更新汇报草稿（5.24）
 * - 不传 id：新建草稿，返回新草稿的 id（汇报 ID）
 * - 传 id：全量覆盖更新，未传字段会清空原值，建议先调 draftDetail 取回完整数据再更新
 * - 返回的 id 为 Java Long 类型，JS 以 string 传递，勿转为 number（精度丢失风险）
 */
export async function draftSave(input: DraftSaveInput): Promise<DraftSaveOutput> {
  if (!input.main?.trim()) return { success: false, message: '标题不能为空' };
  if (!input.contentHtml?.trim()) return { success: false, message: '正文不能为空' };
  try {
    const result = await cworkClient.saveDraft(input);
    return { success: true, data: { id: String(result.id) } };
  } catch (err) {
    return { success: false, message: String(err) };
  }
}
