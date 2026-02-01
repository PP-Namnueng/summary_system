/**
 * TypeScript types matching FastAPI Pydantic models
 * These types ensure type safety when calling the backend API
 */

// ============== Request Types ==============

export interface SummarizeRequest {
    url?: string;
    text?: string;
    language?: string;
    template?: 'standard' | 'executive' | 'technical' | 'eli5';
    model?: string;
    ctx_size?: number;
    contentType?: 'youtube' | 'webpage' | 'pdf';
    contextSize?: number;
}

export interface ChatRequest {
    message: string;
    context?: string;
    history?: Array<{ role: string; content: string }>;
    model?: string;
    use_library_rag?: boolean;
    contextSize?: number;
}

export interface ResearchRequest {
    topic: string;
    language?: string;
    max_sources?: number;
    model?: string;
}

export interface LibrarySearchRequest {
    query: string;
    top_k?: number;
}

// ============== Response Types ==============

export interface SummarizeResponse {
    success: boolean;
    summary?: string;
    title?: string;
    error?: string;
}

export interface ChatResponse {
    success: boolean;
    response?: string;
    error?: string;
}

export interface ResearchResponse {
    success: boolean;
    report?: string;
    sources?: Array<{
        title: string;
        url: string;
        snippet?: string;
    }>;
    error?: string;
}

export interface LibrarySearchResponse {
    success: boolean;
    results?: Array<{
        title: string;
        text: string;
        metadata?: Record<string, unknown>;
    }>;
    error?: string;
}

export interface LibraryStatsResponse {
    total_documents: number;
    indexed_documents: number;
    total_chunks: number;
}

export interface LibraryDocumentsResponse {
    success: boolean;
    documents?: Array<{
        id: string;
        title: string;
        metadata?: Record<string, unknown>;
    }>;
    error?: string;
}

export interface ModelsResponse {
    success: boolean;
    models?: string[];
    error?: string;
}

export interface HealthResponse {
    status: string;
    service: string;
    version: string;
    endpoints: string[];
}

// ============== Sentinel Types ==============

export interface SentinelSource {
    name: string;
    type: string;
    url?: string;
    tags?: string[];
}

export interface SentinelSourcesResponse {
    success: boolean;
    sources?: SentinelSource[];
    error?: string;
}

export interface TrendingItem {
    title: string;
    description?: string;
    url?: string;
    source?: string;
    timestamp?: string;
}

export interface SentinelTrendingResponse {
    success: boolean;
    trending?: TrendingItem[];
    error?: string;
}

export interface SentinelScanResponse {
    success: boolean;
    results?: TrendingItem[];
    error?: string;
}

// ============== TTS Types ==============

export interface TTSRequest {
    text: string;
    voice?: string;
    output_name?: string;
}

export interface TTSResponse {
    success: boolean;
    audio_path?: string;
    voice?: string;
    error?: string;
}

export interface Voice {
    id: string;
    name: string;
    language: string;
}

export interface VoicesResponse {
    success: boolean;
    voices?: Voice[];
    error?: string;
}

// ============== Obsidian Types ==============

export interface ObsidianExportRequest {
    title: string;
    content: string;
    tags?: string[];
}

export interface ObsidianExportResponse {
    success: boolean;
    path?: string;
    error?: string;
}

export interface ObsidianStatusResponse {
    success: boolean;
    configured?: boolean;
    vault_path?: string;
    error?: string;
}

// ============== Upload Types ==============

export interface UploadResponse {
    success: boolean;
    document_id?: string;
    filename?: string;
    pages?: number;
    error?: string;
}
