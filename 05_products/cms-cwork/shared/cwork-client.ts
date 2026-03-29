/**
 * CWork API 客户端
 * 统一封装 CWork 平台 API 调用
 * 懒加载：首次调用时才从环境变量读取配置
 */

import type {
  ApiResult,
  EmpSearchResponse,
  ReportDetail,
  ReportListParams,
  PaginatedResult,
  ReportListItem,
  TaskListParams,
  TaskListItem,
  TaskDetail,
  TodoListParams,
  TodoListItem,
} from './types.js';

/**
 * CWork API 客户端类
 * 懒加载，首次调用时从环境变量读取配置
 */
export class CWorkClient {
  private get baseUrl(): string {
    return process.env['CWORK_BASE_URL'] ?? 'https://sg-al-cwork-web.mediportal.com.cn';
  }

  private get appKey(): string {
    const key = process.env['CWORK_APP_KEY'];
    if (!key) throw new Error('[cwork] 请先调用 setup({ appKey: "xxx" }) 初始化');
    return key;
  }

  private buildUrl(path: string): string {
    return `${this.baseUrl}${path}`;
  }

  private getHeaders(): Record<string, string> {
    return { appKey: this.appKey };
  }

  private getJsonHeaders(): Record<string, string> {
    return { ...this.getHeaders(), 'Content-Type': 'application/json' };
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    const result = await response.json() as ApiResult<T>;
    if (result.resultCode !== 1) throw new Error(`API Error (${result.resultCode}): ${result.resultMsg || '未知错误'}`);
    return result.data;
  }

  private async get<T>(path: string, params?: Record<string, string | number>): Promise<T> {
    const url = new URL(this.buildUrl(path));
    url.searchParams.append('appKey', this.appKey);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) url.searchParams.append(key, String(value));
      });
    }
    return this.handleResponse<T>(await fetch(url.toString(), { method: 'GET', headers: this.getHeaders() }));
  }

  private async post<T>(path: string, body?: Record<string, unknown>): Promise<T> {
    return this.handleResponse<T>(await fetch(this.buildUrl(path), {
      method: 'POST',
      headers: this.getJsonHeaders(),
      body: body ? JSON.stringify(body) : undefined,
    }));
  }

  async searchEmpByName(searchKey: string): Promise<EmpSearchResponse> {
    return this.get<EmpSearchResponse>('/open-api/cwork-user/searchEmpByName', { searchKey });
  }

  async getInboxList(params: ReportListParams): Promise<PaginatedResult<ReportListItem>> {
    return this.post<PaginatedResult<ReportListItem>>('/open-api/work-report/report/record/inbox', params);
  }

  async getReportInfo(reportId: string): Promise<ReportDetail> {
    return this.get<ReportDetail>('/open-api/work-report/report/info', { reportId });
  }

  async searchTaskPage(params: TaskListParams): Promise<PaginatedResult<TaskListItem>> {
    return this.post<PaginatedResult<TaskListItem>>('/open-api/work-report/report/plan/searchPage', params);
  }

  async listCreatedFeedbacks(pageNum: number, pageSize: number): Promise<PaginatedResult<TodoListItem>> {
    return this.post<PaginatedResult<TodoListItem>>('/open-api/work-report/todoTask/listCreatedFeedbacks', { pageNum, pageSize });
  }

  async getSimplePlanAndReportInfo(planId: string): Promise<TaskDetail> {
    return this.get<TaskDetail>('/open-api/work-report/report/plan/getSimplePlanAndReportInfo', { planId });
  }

  async getOutboxList(params: ReportListParams): Promise<PaginatedResult<ReportListItem>> {
    return this.post<PaginatedResult<ReportListItem>>('/open-api/work-report/report/record/outbox', params);
  }

  async getTodoList(params: TodoListParams): Promise<PaginatedResult<TodoListItem>> {
    return this.post<PaginatedResult<TodoListItem>>('/open-api/work-report/reportInfoOpenQuery/todoList', params);
  }

  async completeTodo(todoId: string, content: string, operate?: string): Promise<boolean> {
    return this.post<boolean>('/open-api/work-report/open-platform/todo/completeTodo', { appKey: this.appKey, todoId, content, operate });
  }

  async aiSseQa(userContent: string, reportIdList: string[], aiType?: number): Promise<Response> {
    const response = await fetch(this.buildUrl('/open-api/work-report/open-platform/report/aiSseQaV2'), {
      method: 'POST',
      headers: this.getJsonHeaders(),
      body: JSON.stringify({ appKey: this.appKey, userContent, reportIdList, aiType }),
    });
    if (!response.ok) throw new Error(`SSE Connection Failed: ${response.statusText}`);
    return response;
  }

  async createPlan(params: {
    main: string; needful: string; typeId: number; reportEmpIdList: string[]; target: string; endTime: number;
    ownerEmpIdList?: string[]; assistEmpIdList?: string[]; supervisorEmpIdList?: string[];
    copyEmpIdList?: string[]; observerEmpIdList?: string[]; pushNow?: number;
  }): Promise<string> {
    return this.post<string>('/open-api/work-report/open-platform/report/plan/create', { appKey: this.appKey, ...params });
  }

  async listTemplates(beginTime?: number, endTime?: number, limit?: number): Promise<{ recentOperateTemplates: Array<{ templateId: number; main: string }> }> {
    return this.post('/open-api/work-report/template/listTemplates', { appKey: this.appKey, beginTime, endTime, limit });
  }

  async submitReport(params: {
    main: string; contentHtml: string; contentType?: string; typeId?: number; grade?: string;
    privacyLevel?: string; planId?: string; templateId?: number;
    acceptEmpIdList?: string[]; copyEmpIdList?: string[];
    reportLevelList?: Array<{ type: string; level: number; nodeName: string; levelUserList: Array<{ empId: string }> }>;
    fileVOList?: Array<{ fileId?: string; name: string; type: string; fsize?: number; url?: string }>;
  }): Promise<{ id: string }> {
    return this.post('/open-api/work-report/report/record/submit', { appKey: this.appKey, ...params });
  }

  async uploadFile(file: File): Promise<{ fileId: string }> {
    const formData = new FormData();
    formData.append('file', file);
    const url = `${this.baseUrl}/open-api/cwork-file/uploadWholeFile`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'appKey': this.appKey },
      body: formData,
    });
    const result: ApiResult<string> = await response.json();
    if (result.resultCode !== 1) {
      throw new Error(result.resultMsg ?? '文件上传失败');
    }
    return { fileId: String(result.data) };
  }

  async replyReport(params: {
    reportRecordId: string;
    contentHtml: string;
    addEmpIdList?: string[];
    sendMsg?: boolean;
  }): Promise<number> {
    return this.post<number>('/open-api/work-report/report/record/reply', { appKey: this.appKey, ...params });
  }

  async markReportRead(reportId: number | string): Promise<void> {
    return this.get<void>(`/open-api/work-report/open-platform/report/readReport?reportId=${reportId}`);
  }

  async getUnreadList(params: { pageIndex: number; pageSize: number }): Promise<PaginatedResult<any>> {
    return this.post<PaginatedResult<any>>('/open-api/work-report/reportInfoOpenQuery/unreadList', params);
  }

  async isReportRead(reportId: number | string, employeeId: number | string): Promise<boolean> {
    return this.get<boolean>(`/open-api/work-report/reportInfoOpenQuery/isReportRead?reportId=${reportId}&employeeId=${employeeId}`);
  }

  async listTemplatesByIds(templateIds: Array<number | string>): Promise<Array<{ templateId: number; main: string }>> {
    const response = await fetch(this.buildUrl('/open-api/work-report/template/listByIds'), {
      method: 'POST',
      headers: this.getJsonHeaders(),
      body: JSON.stringify(templateIds),
    });
    return this.handleResponse<Array<{ templateId: number; main: string }>>(response);
  }

  // 联系人分组：查询所有分组
  async queryContactGroups(checkEmpId?: number): Promise<any[]> {
    const payload: Record<string, unknown> = {};
    if (checkEmpId !== undefined) payload['checkEmpId'] = checkEmpId;
    const result = await this.post<any>('/open-api/cwork-user/group/queryTargetUserGroups', payload);
    return Array.isArray(result) ? result : [];
  }

  // 联系人分组：创建或更新分组（id为空=创建，有id=重命名）
  async saveOrUpdateContactGroup(name: string, id?: number): Promise<any> {
    const payload: Record<string, unknown> = { name };
    if (id !== undefined) payload['id'] = id;
    return this.post<any>('/open-api/cwork-user/group/saveOrUpdatePersonalGroup', payload);
  }

  // 联系人分组：增删成员
  async manageGroupMembers(groupId: number, addEmpIds: number[], removeEmpIds: number[]): Promise<any> {
    return this.post<any>('/open-api/cwork-user/group/manageGroupMembers', {
      groupId,
      addEmpIds,
      removeEmpIds,
    });
  }

  // -------------------------------------------------------------------------
  // 草稿箱 (5.24-5.27)
  // -------------------------------------------------------------------------

  /**
   * 5.24 新增或更新汇报草稿（全量覆盖，更新时必须传 id）
   * @returns id — Java Long 类型，JS 中以 string 传递，勿转为 number（> 2^53 会精度截断）
   */
  async saveDraft(params: import('./types.js').SaveDraftParams): Promise<{ id: string }> {
    return this.post<{ id: string }>('/open-api/work-report/draftBox/saveOrUpdate', params as unknown as Record<string, unknown>);
  }

  /** 5.25 草稿箱分页查询 */
  async listDrafts(params: { pageIndex: number; pageSize: number }): Promise<import('./types.js').PaginatedResult<import('./types.js').DraftListItem>> {
    return this.post('/open-api/work-report/draftBox/listByPage', params);
  }

  /** 5.26 草稿汇报详情（reportRecordId = 5.24返回的 id / 5.25列表的 businessId） */
  async getDraftDetail(reportRecordId: string): Promise<import('./types.js').DraftDetail> {
    return this.get<import('./types.js').DraftDetail>(`/open-api/work-report/draftBox/detail/${reportRecordId}`);
  }

  /** 5.27 删除草稿（id = 5.25列表的 id，不是 businessId） */
  async deleteDraft(draftId: string): Promise<boolean> {
    return this.post<boolean>(`/open-api/work-report/draftBox/delete/${draftId}`);
  }
}

// 懒加载 proxy，确保首次调用前不读取环境变量
let _client: CWorkClient | null = null;
function getClient(): CWorkClient {
  if (!_client) _client = new CWorkClient();
  return _client;
}

export const cworkClient = new Proxy({} as CWorkClient, {
  get(_, prop) {
    return (getClient() as any)[prop];
  },
});
