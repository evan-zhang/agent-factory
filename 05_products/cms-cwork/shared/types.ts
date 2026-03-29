/**
 * CWork Skill Package - 通用类型定义
 */

// =============================================================================
// 通用类型
// =============================================================================

export interface ApiResult<T> {
  resultCode: number;
  resultMsg: string | null;
  data: T;
}

export interface PaginatedResult<T> {
  total: number;
  list: T[];
  pageIndex: number;
  pageSize: number;
  size: number;
}

export interface SkillResult<T> {
  success: boolean;
  data?: T;
  message?: string;
}

// =============================================================================
// 员工相关 (4.01)
// =============================================================================

export interface Employee {
  id: string;
  personId: string;
  name: string;
  title: string;
  mainDept: string;
}

export interface EmpSearchResponse {
  inside: {
    empList: Employee[];
  };
  outside: {
    empList: Employee[];
  };
}

// =============================================================================
// 汇报相关 (4.3, 4.5, 4.14)
// =============================================================================

export interface Reply {
  replyId: string;
  content: string;
  replyEmpId: string;
  replyEmpName: string;
  createTime: string;
}

export interface ReportDetail {
  reportId: string;
  content: string;
  createTime: string;
  replies?: Reply[];
}

export interface ReportListItem {
  id: string;
  reportRecordType: number;
  type: string;
  main: string;
  content: string;
  grade: string;
  sendEmpId: string;
  myStatus: number;
  replyCount: number;
  fileCount: number;
  createTime: string;
}

export interface ReportListParams extends Record<string, unknown> {
  pageSize: number;
  pageIndex?: number;
  pageNum?: number;
  reportRecordType?: number;
  empIdList?: string[];
  beginTime?: number;
  endTime?: number;
  readStatus?: number;
  orderColumn?: string;
  grade?: string;
  templateId?: number;
}

// =============================================================================
// 任务相关 (4.11, 4.13)
// =============================================================================

export interface TaskListItem {
  id: string;
  main: string;
  target: string;
  needful: string;
  status: number;
  reportStatus: number;
  reportSubmitCount: number;
  reportTotalCount: number;
  createTime: string;
  endTime: string;
  lastReportTime?: string | number;
  templateId: number;
  reporterList: Employee[];
}

export interface TaskListParams extends Record<string, unknown> {
  pageSize?: number;
  pageIndex?: number;
  keyWord?: string;
  status?: number;
  reportStatus?: number;
  empIdList?: string[];
  grades?: string[];
  labelList?: string[];
  isRead?: number;
  pageNum?: number;
}

export interface TaskDetail {
  id: string;
  main: string;
  needful: string;
  target: string;
  type: string;
  typeId: number;
  planLevel: number;
  status: number;
  endTime: string;
  lastReportTime: string;
  createTime?: string;
  reportList: TaskReportRef[];
}

export interface TaskReportRef {
  id: string;
  main: string;
  createTime: string;
  reportRecordType: number;
}

// =============================================================================
// 待办相关 (4.15)
// =============================================================================

export interface TodoListItem {
  todoId: string;
  main: string;
  title: string;
  status: string;
  createTime: string | number;
  detail: {
    aiSummary?: string;
    progress?: string;
    relatedReportIds?: string[];
  };
}

export interface TodoListParams extends Record<string, unknown> {
  pageIndex: number;
  pageSize: number;
  status?: string;
}

// =============================================================================
// SSE 相关 (4.19)
// =============================================================================

export interface SSEEvent {
  content?: string;
  summary?: string;
}

export interface SSEQuestionParams {
  userContent: string;
  reportIdList: string[];
  aiType?: number;
}

// =============================================================================
// Skill 输入/输出类型
// =============================================================================

// emp-search
export interface EmpSearchInput {
  name: string;
}
export type EmpSearchOutput = SkillResult<Employee[]>;

// report-get-by-id
export interface ReportGetByIdInput {
  reportId: string;
}
export type ReportGetByIdOutput = SkillResult<ReportDetail>;

// inbox-query
export interface InboxQueryInput extends ReportListParams {}
export type InboxQueryOutput = SkillResult<PaginatedResult<ReportListItem>>;

// outbox-query
export interface OutboxQueryInput extends ReportListParams {}
export type OutboxQueryOutput = SkillResult<PaginatedResult<ReportListItem>>;

// task-list-query
export interface TaskListQueryInput extends TaskListParams {}
export type TaskListQueryOutput = SkillResult<PaginatedResult<TaskListItem>>;

// todo-list-query
export interface TodoListQueryInput extends TodoListParams {}
export type TodoListQueryOutput = SkillResult<PaginatedResult<TodoListItem>>;

// task-chain-get
export interface TaskChainGetInput {
  taskId: string;
  maxReports?: number;
}
export interface TaskChainItem {
  reportId: string;
  content: string;
  createTime: string;
}
export interface TaskChainGetOutput {
  taskId: string;
  title: string;
  status: number;
  reports: TaskChainItem[];
  latestUpdate: string;
}
export type TaskChainGetSkillOutput = SkillResult<TaskChainGetOutput>;

// draft-gen
export interface DraftGenInput {
  rawContent: string;
  reportType?: '日报' | '周报' | '阶段汇报';
  targetAudience?: string;
  templateId?: string;
}
export interface DraftGenOutput {
  title: string;
  background?: string;
  progress: string[];
  problems?: string[];
  plan?: string[];
  risks?: string[];
}
export type DraftGenSkillOutput = SkillResult<DraftGenOutput>;

// outline-gen
export interface OutlineGenInput {
  rawContent: string;
  reportType?: '日报' | '周报' | '阶段汇报';
  requirements?: string;
  context?: string;
}
export interface OutlineSection {
  title: string;
  points: string[];
}
export interface OutlineGenOutput {
  sections: OutlineSection[];
  suggestedTitle?: string;
}
export type OutlineGenSkillOutput = SkillResult<OutlineGenOutput>;

// todo-extract
export interface TodoExtractInput {
  source: string;
  sourceType: 'discussion' | 'report';
}
export interface TodoItem {
  description: string;
  suggestedAssignee?: string;
  suggestedDeadline?: string;
}
export type TodoExtractOutput = SkillResult<{ items: TodoItem[] }>;

// task-structure
export interface TaskStructureInput {
  todoDescription: string;
  suggestedAssignee?: string;
  suggestedDeadline?: string;
  needful?: string;
}
export interface TaskDraft {
  title: string;
  content: string;
  target: string;
  assignee?: string;
  assigneeName?: string;
  deadline?: number;
  grades: string;
}
export type TaskStructureOutput = SkillResult<TaskDraft>;

// task-create
export interface TaskCreateInput {
  title: string;
  content: string;
  target: string;
  assignee?: string;              // 责任人（单选）
  deadline?: number;              // 截止时间（时间戳，毫秒）
  grades?: string;               // 优先级：一般/紧急
  reportEmpIdList?: string[];    // 汇报人
  assistEmpIdList?: string[];    // 协办人
  supervisorEmpIdList?: string[]; // 监督人
  copyEmpIdList?: string[];      // 抄送人
  observerEmpIdList?: string[];  // 观察员
  pushNow?: boolean;             // 创建后立即推送通知
}
export type TaskCreateOutput = SkillResult<{ taskId: string }>;

// task-my-assigned
export interface TaskMyAssignedInput {
  userId: string;      // 当前用户 empId
  pageSize?: number;
  pageIndex?: number;
  status?: number;     // 0=关闭、1=进行中、2=未启动
}
export type TaskMyAssignedOutput = SkillResult<{
  total: number;
  list: any[];
  pageIndex: number;
  pageSize: number;
}>;

// task-my-created
export interface TaskMyCreatedInput {
  pageSize?: number;
  pageIndex?: number;
  status?: number;
  /** 按分配对象筛选（如：下属 ID 列表） */
  assigneeIds?: string[];
}
export type TaskMyCreatedOutput = SkillResult<{
  total: number;
  list: any[];
  pageIndex: number;
  pageSize: number;
  filterApplied?: string;
  note?: string;
}>;

// task-manager-dashboard
export interface TaskManagerDashboardInput {
  subordinateIds: string[];  // 下属员工 ID 列表
  pageSize?: number;
  pageIndex?: number;
  taskStatus?: number;    // 任务状态：0=关闭、1=进行中
  reportStatus?: number;  // 汇报状态：0=关闭、1=待汇报、2=已汇报、3=逾期
}
export interface TaskManagerDashboardData {
  summary: {
    total: number;
    inProgress: number;
    closed: number;
    pending: number;   // 待汇报
    overdue: number;   // 逾期
    reported: number;  // 已汇报
  };
  byPerson: Array<{
    empId: string;
    taskCount: number;
    inProgress: number;
    overdue: number;
    tasks: Array<{
      id: number;
      main: string;
      status: number;
      reportStatus: number;
      lastReportTime?: string;
      endTime?: string;
    }>;
  }>;
  total: number;
  pageIndex: number;
  pageSize: number;
}
export type TaskManagerDashboardOutput = SkillResult<TaskManagerDashboardData>;

// task-blocker-identify
export interface TaskBlockerInput {
  taskList?: TaskListItem[];
  pageNum?: number;
  pageSize?: number;
  status?: number;
  empIdList?: string[];
}
export interface BlockerTask {
  taskId: string;
  title: string;
  issue: '逾期' | '无责任人' | '卡点' | '进度滞后';
  severity: '高' | '中' | '低';
  details?: {
    endTime?: string;
    reportStatus?: number;
    reportSubmitCount?: number;
    reportTotalCount?: number;
  };
}
export type TaskBlockerIdentifyOutput = SkillResult<BlockerTask[]>;

// report-rewrite
export interface ReportRewriteInput {
  draftContent: string;
  rewriteType: 'structure' | 'expression' | 'simplify';
  instruction?: string;
}
export type ReportRewriteOutput = SkillResult<{ original: string; rewritten: string; changes: string[] }>;

// report-complete
export interface ReportCompleteInput {
  draftContent: string;
  missingFields?: string[];
}
export interface CompletedReport {
  title?: string;
  background?: string;
  progress: string[];
  problems: string[];
  plan: string[];
  risks: string[];
}
export type ReportCompleteOutput = SkillResult<CompletedReport>;

// report-tone-adapt
export interface ReportToneAdaptInput {
  draftContent: string;
  audience: '直属上级' | '管理层' | '跨部门' | '外部';
}
export type ReportToneAdaptOutput = SkillResult<{ adapted: string; explanation: string }>;

// report-submit
export interface ReportSubmitInput {
  main: string;
  contentHtml: string;
  contentType?: 'html' | 'markdown';
  typeId?: number;
  grade?: '一般' | '紧急';
  acceptEmpIdList?: string[];
  copyEmpIdList?: string[];
  reportLevelList?: Array<{
    type: 'read' | 'suggest' | 'decide';
    level: number;
    nodeName: string;
    levelUserList: Array<{ empId: string }>;
  }>;
  fileVOList?: Array<{
    fileId?: string;
    name: string;
    type: 'file' | 'url';
    fsize?: number;
    url?: string;
  }>;
}
export type ReportSubmitOutput = SkillResult<{ reportId: string }>;

export type FileUploadOutput = SkillResult<{ fileId: string; fileName: string; fileSize: number }>;

export interface ReportPrepareInput {
  main: string;
  contentHtml: string;
  contentType?: 'html' | 'markdown';
  typeId?: number;
  grade?: '一般' | '紧急';
  acceptEmpIdList?: string[];
  copyEmpIdList?: string[];
  reportLevelList?: Array<{
    type: 'read' | 'suggest' | 'decide';
    level: number;
    nodeName: string;
    levelUserList: Array<{ empId: string }>;
  }>;
  filePaths?: string[];
  fileNames?: string[];
}
export interface ReportPrepareOutputData {
  confirmInfo: {
    main: string;
    contentHtml: string;
    contentType: string;
    typeId: number;
    grade: string;
    acceptEmpIdList: string[];
    copyEmpIdList: string[];
    reportLevelList: Array<{
      type: string;
      level: number;
      nodeName: string;
      levelUserList: Array<{ empId: string }>;
    }>;
    previewText: string;
    attachmentSummary: string;
    attachmentCount: number;
    confirmPrompt: string;
  };
}
export type ReportPrepareOutput = SkillResult<ReportPrepareOutputData>;

export interface ReportValidateReceiversInput {
  /** 待校验的接收人姓名列表（模糊搜索） */
  names: string[];
}
export interface ReportValidateReceiversOutputData {
  validatedCount: number;
  /** 已确认的员工列表（可直接传给 reportSubmit） */
  confirmedEmployees: Array<{ empId: string; name: string; title: string; dept: string }>;
  confirmPrompt: string;
}
export type ReportValidateReceiversOutput = SkillResult<ReportValidateReceiversOutputData>;

// report-remind
export interface ReportRemindInput {
  empId: string;         // 被催办人 empId
  taskMain: string;      // 任务名称
  deadline?: number;     // 截止时间（时间戳）
  content?: string;      // 自定义催办内容
}
export type ReportRemindOutput = SkillResult<{ reportId: string; remindedEmpId: string; message: string }>;

// todo-complete
export interface TodoCompleteInput {
  todoId: string;
  content?: string;
  /** 决策类必填：agree=同意，disagree=不同意 */
  operate?: 'agree' | 'disagree';
}
export type TodoCompleteOutput = SkillResult<{ todoId: string; operate?: string; message: string }>;

// report-reply
export interface ReportReplyInput {
  reportRecordId: string;
  contentHtml: string;
  addEmpIdList?: string[];
  sendMsg?: boolean;
}
export type ReportReplyOutput = SkillResult<{ replyId: string }>;

// template-list
export interface TemplateListInput {
  beginTime?: number;
  endTime?: number;
  limit?: number;
}
export type TemplateListOutput = SkillResult<{
  total: number;
  list: Array<{ templateId: string; main: string }>;
}>;

// report-read-mark
export interface ReportReadMarkInput { reportId: string }
export type ReportReadMarkOutput = SkillResult<{ reportId: string; message: string }>;

// unread-report-list
export interface UnreadReportListInput { pageSize?: number; pageIndex?: number }
export type UnreadReportListOutput = SkillResult<{
  total: number;
  list: any[];
  pageIndex: number;
  pageSize: number;
}>;

// report-is-read
export interface ReportIsReadInput { reportId: string; employeeId: string }
export type ReportIsReadOutput = SkillResult<{
  reportId: string;
  employeeId: string;
  isRead: boolean;
  status: string;
}>;

// ai-report-chat
export interface AiReportChatInput {
  reportIdList: string[];
  userContent: string;
  aiType?: number;
}
export type AiReportChatOutput = SkillResult<{
  stream: Response;
  reportCount: number;
  message: string;
}>;

// my-feedback-list
export interface MyFeedbackListInput { pageSize?: number; pageIndex?: number }
export type MyFeedbackListOutput = SkillResult<{
  total: number;
  list: any[];
  pageIndex: number;
  pageSize: number;
}>;

// template-info-batch
export interface TemplateInfoBatchInput { templateIds: string[] }
export type TemplateInfoBatchOutput = SkillResult<{
  total: number;
  list: Array<{ templateId: string; main: string }>;
}>;

export interface ReportSubmitWithAttachmentsInput {
  main: string;
  contentHtml: string;
  contentType?: 'html' | 'markdown';
  typeId?: number;
  grade?: '一般' | '紧急';
  acceptEmpIdList?: string[];
  copyEmpIdList?: string[];
  reportLevelList?: Array<{
    type: 'read' | 'suggest' | 'decide';
    level: number;
    nodeName: string;
    levelUserList: Array<{ empId: string }>;
  }>;
  /** 本地文件路径列表，建议不超过10个 */
  filePaths: string[];
  /** 对应的文件名列表，数量必须与 filePaths 一致 */
  fileNames: string[];
}
export type ReportSubmitWithAttachmentsOutput = SkillResult<{ reportId: string; uploadedFiles: number }>;

// ai-highlight-extract
export interface AiHighlightExtractInput {
  reportIdList: string[];
}
export interface HighlightItem {
  content: string;
  sourceReport: string;
}
export type AiHighlightExtractOutput = SkillResult<{ highlights: string[]; sourceReports: string[] }>;

// ai-problem-identify
export interface AiProblemIdentifyInput {
  reportIdList: string[];
}
export interface ProblemItem {
  description: string;
  severity: '高' | '中' | '低';
  sourceReport: string;
}
export type AiProblemIdentifyOutput = SkillResult<{ problems: ProblemItem[] }>;

// ai-risk-identify
export interface AiRiskIdentifyInput {
  reportIdList: string[];
}
export interface RiskItem {
  description: string;
  probability: '高' | '中' | '低';
  impact: '高' | '中' | '低';
}
export type AiRiskIdentifyOutput = SkillResult<{ risks: RiskItem[] }>;

// ai-compare-reports
export interface AiCompareReportsInput {
  reportIdList: string[];
  timeRange?: { begin: number; end: number };
}
export interface ComparisonItem {
  topic: string;
  trend: '改善' | '稳定' | '恶化' | '波动';
  description: string;
}
export type AiCompareReportsOutput = SkillResult<{ summary: string; comparison: ComparisonItem[] }>;

// decision-conclusion-extract
export interface DecisionConclusionExtractInput {
  todoDetail: { title: string; aiSummary?: string; status: string };
  relatedReports: Array<{
    reportId: string;
    content: string;
    replies?: Array<{ content: string; replyEmpName: string; createTime: string }>;
  }>;
}
export interface ConclusionItem {
  content: string;
  source: 'todo' | 'report';
  confidence: '高' | '中' | '低';
}
export type DecisionConclusionExtractOutput = SkillResult<{ conclusions: ConclusionItem[] }>;

// decision-resolved-pending
export interface DecisionResolvedPendingInput {
  todoStatus: string;
  conclusions: Array<{ content: string; confidence: string }>;
}
export interface ResolvedPendingItem {
  content: string;
  status: '已决' | '待决';
  reason: string;
}
export type DecisionResolvedPendingOutput = SkillResult<{
  resolved: ResolvedPendingItem[];
  pending: ResolvedPendingItem[];
  summary: string;
}>;

// decision-summary-gen
export interface DecisionSummaryGenInput {
  todoId: string;
  resolved: Array<{ content: string; status: string; reason: string }>;
  pending: Array<{ content: string; status: string; reason: string }>;
  stateFlow?: Array<{ state: string; time: number; evidence: string }>;
}
export interface DecisionSummary {
  title: string;
  decision: string;
  resolvedPoints: string[];
  pendingPoints: string[];
  actionItems: string[];
}
export type DecisionSummaryGenOutput = SkillResult<DecisionSummary>;

// =============================================================================
// 草稿相关 (5.24-5.27)
// =============================================================================

export interface DraftEmployee {
  empId: string;
  name: string;
  title?: string;
  mainDept?: string;
}

export interface DraftFileVO {
  fileId?: string;
  name: string;
  type?: string;
  fsize?: number;
  url?: string;
}

export interface DraftReportLevelParam {
  level: number;
  type: string;       // suggest | decide | read
  nodeCode?: string;
  nodeName?: string;
  levelUserList?: Array<{ empId: string; requirement?: string }>;  // 存草稿时传入
  empList?: Array<{ empId: string; name?: string; requirement?: string }>;  // 服务端返回时实际字段名（文档写 levelUserList 但实际是 empList）
}

export interface SaveDraftParams {
  id?: string;                                 // 更新时必填；不传=新增
  main: string;                                // 标题（必填）
  contentHtml: string;                         // 正文（必填）
  contentType?: string;                        // 默认 markdown
  typeId?: number;                             // 默认 9999
  grade?: string;                              // 一般 | 紧急
  privacyLevel?: string;                       // 非涉密 | 涉密
  planId?: string;
  templateId?: string;
  acceptEmpIdList?: string[];
  copyEmpIdList?: string[];
  reportLevelList?: DraftReportLevelParam[];
  fileVOList?: DraftFileVO[];
}

export interface DraftDetail {
  id: string;
  main: string;
  contentHtml: string;
  contentType?: string;
  typeId?: number;
  grade?: string;
  privacyLevel?: string;
  reportCode?: string;
  reportRecordType?: number;
  status?: number;
  acceptEmployeeList: DraftEmployee[] | null;   // 服务端无接收人时返回 null 而非 []
  copyEmployeeList: DraftEmployee[] | null;     // 同上
  reportLevelList: DraftReportLevelParam[] | null;
  fileList: DraftFileVO[] | null;
}

export interface DraftListItem {
  id: string;           // 草稿 ID（用于 delete）
  bizType: string;      // 通常为 "report"
  businessId: string;  // 汇报 ID（用于 detail）
  main?: string;
  createTime?: string;
  updateTime?: string;
}

// judge-closure-status
export interface JudgeClosureStatusInput {
  itemId: string;
  itemType: 'task' | 'decision' | 'feedback';
  followupChain: {
    timeline: Array<{ nodeType: string; nodeId: string; content: string; time: number }>;
  };
  deadline?: number;
}
export interface ClosureJudgment {
  isClosed: boolean;
  closedAt?: number;
  evidence: string[];
  reasoning: string;
  confidence: '高' | '中' | '低';
}
export type JudgeClosureStatusOutput = SkillResult<ClosureJudgment>;

// identify-unclosed-items
export interface IdentifyUnclosedItemsInput {
  itemIds: string[];
  itemType: 'task' | 'decision' | 'feedback';
  daysThreshold?: number;
}
export interface UnclosedItem {
  itemId: string;
  itemType: string;
  owner?: string;
  daysUnresolved: number;
  lastFeedback?: string;
  suggestedAction: string;
}
export type IdentifyUnclosedItemsOutput = SkillResult<UnclosedItem[]>;

// generate-unclosed-list
export interface GenerateUnclosedListInput {
  unclosedItems: UnclosedItem[];
}
export interface UnclosedListSummary {
  summary: string;
  list: UnclosedItem[];
  priority: '高' | '中' | '低';
}
export type GenerateUnclosedListOutput = SkillResult<UnclosedListSummary>;

// reminder-tip
export interface ReminderTipInput {
  itemId: string;
  itemType: 'task' | 'decision' | 'feedback';
  recipient: string;
  daysUnresolved: number;
  originalRequest?: string;
  reminderStyle?: 'polite' | 'urgent' | 'formal';
  context?: string;
}
export interface ReminderTip {
  subject: string;
  message: string;
  suggestedActions: string[];
  tone: 'friendly' | 'neutral' | 'urgent';
}
export type ReminderTipOutput = SkillResult<ReminderTip>;

// summarize-followup-status
export interface SummarizeFollowupStatusInput {
  itemId: string;
  itemType: 'task' | 'decision' | 'feedback';
  followupChain: Array<{
    nodeType: string;
    nodeId: string;
    content: string;
    author?: string;
    time: number;
  }>;
  deadline?: number;
}
export interface FollowupStatusSummary {
  status: 'closed' | 'in_progress' | 'stalled' | 'blocked';
  progress: string;
  latestUpdate: string;
  timeSinceLastUpdate: number;
  milestones: Array<{ time: number; event: string; description: string }>;
  blockers: string[];
  nextSteps: string[];
  estimatedCompletion?: number;
}
export type SummarizeFollowupStatusOutput = SkillResult<FollowupStatusSummary>;

// summary-trends
export interface SummaryTrendsInput {
  reports: Array<{ reportId: string; submitTime: number; content: string; employeeName?: string }>;
  focusAreas?: string[];
}
export interface TrendSummary {
  overallTrend: 'improving' | 'stable' | 'declining' | 'fluctuating';
  keyMetrics: Array<{ metric: string; trend: 'up' | 'down' | 'stable'; description: string }>;
  patternInsights: string[];
  recommendations: string[];
}
export type SummaryTrendsOutput = SkillResult<TrendSummary>;

// format-analysis-output
export interface FormatAnalysisOutputInput {
  analysisType: 'highlight' | 'problem' | 'risk' | 'compare';
  highlights?: { highlights: Array<{ category: string; content: string; important: boolean }>; summary: string };
  problems?: { problems: Array<{ description: string; severity: 'high' | 'medium' | 'low'; suggestions?: string[] }> };
  risks?: { risks: Array<{ description: string; level: 'high' | 'medium' | 'low'; probability: 'high' | 'medium' | 'low'; impact: 'high' | 'medium' | 'low'; mitigation?: string }> };
  compareResult?: string;
  reportTitle?: string;
  analysisTime?: number;
}
export type FormatAnalysisOutputOutput = SkillResult<string>;

// discussion-thread
export interface DiscussionThreadInput {
  threadId: string;
  messages: Array<{ author: string; content: string; timestamp: number }>;
  focusQuestion?: string;
}
export interface DiscussionSummary {
  topic: string;
  participants: string[];
  timeline: Array<{ time: number; author: string; keyPoint: string }>;
  keyViewpoints: Array<{ viewpoint: string; supporters: string[]; argument: string }>;
  conclusions: string[];
  openQuestions: string[];
}
export type DiscussionThreadOutput = SkillResult<DiscussionSummary>;

// decision-format-standardize
export interface DecisionFormatStandardizeInput {
  decisionId: string;
  title: string;
  decision: string;
  resolvedPoints?: string[];
  pendingPoints?: string[];
  actionItems?: string[];
  participants?: string[];
  decisionTime?: number;
}
export type DecisionFormatStandardizeOutput = SkillResult<string>;

// task-blocker-tip
export interface TaskBlockerTipInput {
  taskId: string;
  taskTitle: string;
  blockerReason: string;
  daysOverdue: number;
  assignee?: string;
  relatedContext?: string;
}
export interface BlockerTip {
  tip: string;
  suggestedActions: string[];
  escalationRecommend?: '立即升级' | '继续观察' | '安排会议' | '重新分配';
  priority: '紧急' | '高' | '中' | '低';
}
export type TaskBlockerTipOutput = SkillResult<BlockerTip>;

// task-adjustment-suggest
export interface TaskAdjustmentSuggestInput {
  taskId: string;
  taskTitle: string;
  currentProgress: string;
  originalDeadline: number;
  remainingWork: string;
  blockers?: string[];
  resourceConstraints?: string;
}
export interface TaskAdjustment {
  adjustmentType: 'deadline_extend' | 'resource_increase' | 'scope_reduce' | 'priority_change' | 'no_change';
  reasoning: string;
  suggestedDeadline?: number;
  suggestedResources?: string[];
  suggestedScope?: string;
  priorityChange?: 'raise' | 'lower' | 'maintain';
}
export type TaskAdjustmentSuggestOutput = SkillResult<TaskAdjustment>;

// report-format
export interface ReportFormatInput {
  title: string;
  progress?: string;
  problems?: string;
  plan?: string;
  risks?: string;
  formatTemplate?: 'standard' | 'simple' | 'detailed';
}
export type ReportFormatOutput = SkillResult<string>;

// report-formality-adjust
export interface ReportFormalityAdjustInput {
  content: string;
  targetFormality: 'formal' | 'semi-formal' | 'informal';
  reportType?: string;
}
export type ReportFormalityAdjustOutput = SkillResult<string>;

// SSE client
export interface SSEClientInput {
  reportIdList: string[];
  question: string;
}
export type SSEClientOutput = SkillResult<{ content: string; isComplete: boolean; summary?: string }>;

// multi-source-agg
export interface MultiSourceAggInput {
  timeRange?: { start: number; end: number };
  employeeIds?: string[];
  focusAreas?: string[];
  includeCompleted?: boolean;
}
export interface WorkSummary {
  period: string;
  overview: string;
  tasks: { total: number; completed: number; inProgress: number; overdue: number; highlights: string[] };
  reports: { total: number; keyInsights: string[]; problems: string[]; risks: string[] };
  decisions: { total: number; resolved: string[]; pending: string[] };
  trends: { positive: string[]; concerning: string[] };
  recommendations: string[];
}
export type MultiSourceAggOutput = SkillResult<WorkSummary>;

// ===== contacts 联系人分组 =====
export interface ContactGroup {
  groupId: number;
  groupName: string;
  memberCount?: number;
  members?: ContactGroupMember[];
}

export interface ContactGroupMember {
  empId: number;
  name: string;
  deptName?: string;
}

export interface ContactGroupListInput {
  checkEmpId?: number;
}
export type ContactGroupListOutput = SkillResult<{ groups: ContactGroup[] }>;

export interface ContactGroupCreateInput {
  name: string;
}
export type ContactGroupCreateOutput = SkillResult<{ groupId?: number }>;

export interface ContactGroupRenameInput {
  groupName: string;   // 原分组名（用于查找 groupId）
  newName: string;
}
export type ContactGroupRenameOutput = SkillResult<{}>;

export interface ContactGroupMembersInput {
  groupName: string;   // 分组名（用于查找 groupId）
  addNames?: string[]; // 新增成员姓名列表
  removeNames?: string[]; // 移除成员姓名列表
}
export type ContactGroupMembersOutput = SkillResult<{}>;
