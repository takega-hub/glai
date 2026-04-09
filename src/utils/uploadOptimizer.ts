import sharp from 'sharp';
import { v4 as uuidv4 } from 'uuid';
import path from 'path';
import { promises as fs } from 'fs';
import { ImageOptimizer } from './imageOptimizer';

export interface UploadOptimizerOptions {
  destination: string;
  maxFileSize?: number;
  allowedFormats?: string[];
  createWebVersion?: boolean;
  createThumbnail?: boolean;
  webQuality?: number;
  thumbnailQuality?: number;
  webMaxWidth?: number;
  webMaxHeight?: number;
  thumbnailSize?: number;
}

const DEFAULT_OPTIONS: UploadOptimizerOptions = {
  destination: './uploads',
  maxFileSize: 10 * 1024 * 1024, // 10MB
  allowedFormats: ['image/jpeg', 'image/png', 'image/webp'],
  createWebVersion: true,
  createThumbnail: true,
  webQuality: 75,
  thumbnailQuality: 70,
  webMaxWidth: 1200,
  webMaxHeight: 800,
  thumbnailSize: 300
};

export class UploadOptimizer {
  private options: UploadOptimizerOptions;

  constructor(options: Partial<UploadOptimizerOptions> = {}) {
    this.options = { ...DEFAULT_OPTIONS, ...options };
  }

  async processImageBuffer(
    buffer: Buffer,
    originalName: string
  ): Promise<{
    original: string | null;
    web: string | null;
    thumbnail: string | null;
    fileName: string;
  }> {
    const fileName = uuidv4();
    const originalExt = path.extname(originalName);
    
    const results = {
      original: null as string | null,
      web: null as string | null,
      thumbnail: null as string | null,
      fileName
    };

    try {
      // Ensure destination directory exists
      await fs.mkdir(this.options.destination, { recursive: true });

      // Save original file
      const originalPath = path.join(this.options.destination, `${fileName}_original${originalExt}`);
      await sharp(buffer).toFile(originalPath);
      results.original = originalPath;

      // Create web-optimized version
      if (this.options.createWebVersion) {
        const webOptimizer = new ImageOptimizer({
          quality: this.options.webQuality,
          maxWidth: this.options.webMaxWidth,
          maxHeight: this.options.webMaxHeight,
          format: 'webp',
          preserveOriginal: true
        });

        const webPath = path.join(this.options.destination, `${fileName}_web.webp`);
        await webOptimizer.optimizeImage(originalPath, webPath);
        results.web = webPath;
      }

      // Create thumbnail
      if (this.options.createThumbnail) {
        const thumbnailOptimizer = new ImageOptimizer({
          quality: this.options.thumbnailQuality,
          maxWidth: this.options.thumbnailSize,
          maxHeight: this.options.thumbnailSize,
          format: 'webp',
          preserveOriginal: true
        });

        const thumbnailPath = path.join(this.options.destination, `${fileName}_thumbnail.webp`);
        await thumbnailOptimizer.optimizeImage(originalPath, thumbnailPath);
        results.thumbnail = thumbnailPath;
      }

      return results;
    } catch (error) {
      // Clean up any created files on error
      if (results.original) {
        try {
          await fs.unlink(results.original);
        } catch (cleanupError) {
          console.error('Failed to clean up original file:', cleanupError);
        }
      }
      throw error;
    }
  }
}

// Utility function for single file optimization
export async function optimizeUploadedFile(
  filePath: string,
  options: Partial<UploadOptimizerOptions> = {}
) {
  const mergedOptions = { ...DEFAULT_OPTIONS, ...options };
  const results: any = {};

  if (mergedOptions.createWebVersion) {
    const webOptimizer = new ImageOptimizer({
      quality: mergedOptions.webQuality,
      maxWidth: mergedOptions.webMaxWidth,
      maxHeight: mergedOptions.webMaxHeight,
      format: 'webp',
      preserveOriginal: true
    });

    const webPath = filePath.replace(/\.(png|jpe?g)$/i, '_web.webp');
    results.web = await webOptimizer.optimizeImage(filePath, webPath);
  }

  if (mergedOptions.createThumbnail) {
    const thumbnailOptimizer = new ImageOptimizer({
      quality: mergedOptions.thumbnailQuality,
      maxWidth: mergedOptions.thumbnailSize,
      maxHeight: mergedOptions.thumbnailSize,
      format: 'webp',
      preserveOriginal: true
    });

    const thumbnailPath = filePath.replace(/\.(png|jpe?g)$/i, '_thumbnail.webp');
    results.thumbnail = await thumbnailOptimizer.optimizeImage(filePath, thumbnailPath);
  }

  return results;
}