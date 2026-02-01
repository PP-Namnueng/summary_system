/**
 * API Client for Knowledge Summary System
 * Connects to FastAPI backend without modifying any service logic
 */

import axios, { AxiosInstance } from 'axios';
import type {
    SummarizeRequest,
    SummarizeResponse,
    ChatRequest,
    ChatResponse,
    ResearchRequest,
    ResearchResponse,
    LibrarySearchRequest,
    LibrarySearchResponse,
    LibraryStatsResponse,
    LibraryDocumentsResponse,
    ModelsResponse,
    HealthResponse,
} from './types';

class APIClient {
    private client: AxiosInstance;

    constructor(baseURL?: string) {
        this.client = axios.create({
            baseURL: baseURL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
            headers: {
                'Content-Type': 'application/json',
            },
            timeout: 300000, // 5 minutes for long-running AI operations
        });
    }

    // ============== Health Check ==============

    async healthCheck(): Promise<HealthResponse> {
        const response = await this.client.get<HealthResponse>('/');
        return response.data;
    }

    // ============== Summarization ==============

    async summarize(request: SummarizeRequest): Promise<SummarizeResponse> {
        const response = await this.client.post<SummarizeResponse>('/summarize', request);
        return response.data;
    }

    // ============== Chat ==============

    async chat(request: ChatRequest): Promise<ChatResponse> {
        const response = await this.client.post<ChatResponse>('/chat', request);
        return response.data;
    }

    // ============== Research ==============

    async research(request: ResearchRequest): Promise<ResearchResponse> {
        const response = await this.client.post<ResearchResponse>('/research', request);
        return response.data;
    }

    // ============== Library ==============

    async librarySearch(request: LibrarySearchRequest): Promise<LibrarySearchResponse> {
        const response = await this.client.post<LibrarySearchResponse>('/library/search', request);
        return response.data;
    }

    async libraryStats(): Promise<LibraryStatsResponse> {
        const response = await this.client.get<LibraryStatsResponse>('/library/stats');
        return response.data;
    }

    async libraryDocuments(): Promise<LibraryDocumentsResponse> {
        const response = await this.client.get<LibraryDocumentsResponse>('/library/documents');
        return response.data;
    }

    // ============== Models ==============

    async listModels(): Promise<ModelsResponse> {
        const response = await this.client.get<ModelsResponse>('/models');
        return response.data;
    }

    async getModels(): Promise<{ models: string[] }> {
        const response = await this.client.get<ModelsResponse>('/models');
        return { models: response.data.models || [] };
    }

    // ============== Sentinel ==============

    async getSentinelSources(): Promise<import('./types').SentinelSourcesResponse> {
        const response = await this.client.get('/sentinel/sources');
        return response.data;
    }

    async getSentinelTrending(): Promise<import('./types').SentinelTrendingResponse> {
        const response = await this.client.get('/sentinel/trending');
        return response.data;
    }

    async triggerSentinelScan(): Promise<import('./types').SentinelScanResponse> {
        const response = await this.client.post('/sentinel/scan');
        return response.data;
    }

    // ============== TTS ==============

    async generateTTS(request: import('./types').TTSRequest): Promise<import('./types').TTSResponse> {
        const response = await this.client.post('/tts/generate', request);
        return response.data;
    }

    async getTTSVoices(): Promise<import('./types').VoicesResponse> {
        const response = await this.client.get('/tts/voices');
        return response.data;
    }

    // ============== Obsidian ==============

    async exportToObsidian(request: import('./types').ObsidianExportRequest): Promise<import('./types').ObsidianExportResponse> {
        const response = await this.client.post('/obsidian/export', request);
        return response.data;
    }

    async getObsidianStatus(): Promise<import('./types').ObsidianStatusResponse> {
        const response = await this.client.get('/obsidian/status');
        return response.data;
    }

    // ============== Upload ==============

    async uploadPDF(file: File): Promise<import('./types').UploadResponse> {
        const formData = new FormData();
        formData.append('file', file);
        const response = await this.client.post('/library/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    }
}

// Export singleton instance
export const apiClient = new APIClient();

// Export class for custom instances
export default APIClient;
