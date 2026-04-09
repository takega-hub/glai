import sharp from 'sharp';
import { promises as fs } from 'fs';
import path from 'path';
const DEFAULT_OPTIONS = {
    quality: 80,
    maxWidth: 1920,
    maxHeight: 1080,
    format: 'webp',
    preserveOriginal: true
};
export class ImageOptimizer {
    constructor(options = {}) {
        Object.defineProperty(this, "options", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        this.options = { ...DEFAULT_OPTIONS, ...options };
    }
    async optimizeImage(inputPath, outputPath) {
        try {
            const originalBuffer = await fs.readFile(inputPath);
            const originalSize = originalBuffer.length;
            let sharpInstance = sharp(inputPath);
            // Resize if dimensions are specified
            if (this.options.maxWidth || this.options.maxHeight) {
                sharpInstance = sharpInstance.resize({
                    width: this.options.maxWidth,
                    height: this.options.maxHeight,
                    fit: 'inside',
                    withoutEnlargement: true
                });
            }
            // Apply format-specific optimizations
            let optimizedBuffer;
            const finalOutputPath = outputPath || this.getOptimizedPath(inputPath);
            switch (this.options.format) {
                case 'webp':
                    optimizedBuffer = await sharpInstance
                        .webp({ quality: this.options.quality })
                        .toBuffer();
                    break;
                case 'jpeg':
                    optimizedBuffer = await sharpInstance
                        .jpeg({ quality: this.options.quality, progressive: true })
                        .toBuffer();
                    break;
                case 'png':
                    optimizedBuffer = await sharpInstance
                        .png({ quality: this.options.quality })
                        .toBuffer();
                    break;
                default:
                    optimizedBuffer = await sharpInstance.toBuffer();
            }
            // Save optimized image
            await fs.writeFile(finalOutputPath, optimizedBuffer);
            const optimizedSize = optimizedBuffer.length;
            const savedPercentage = ((originalSize - optimizedSize) / originalSize) * 100;
            // Remove original if not preserving
            if (!this.options.preserveOriginal && finalOutputPath !== inputPath) {
                await fs.unlink(inputPath);
            }
            return {
                originalSize,
                optimizedSize,
                savedPercentage,
                outputPath: finalOutputPath
            };
        }
        catch (error) {
            throw new Error(`Failed to optimize image ${inputPath}: ${error instanceof Error ? error.message : String(error)}`);
        }
    }
    getOptimizedPath(inputPath) {
        const dir = path.dirname(inputPath);
        const ext = path.extname(inputPath);
        const name = path.basename(inputPath, ext);
        const newExt = this.options.format === 'jpeg' ? '.jpg' : `.${this.options.format}`;
        if (this.options.preserveOriginal) {
            return path.join(dir, `${name}_optimized${newExt}`);
        }
        return path.join(dir, `${name}${newExt}`);
    }
}
// Utility functions for common use cases
export async function optimizeForWeb(imagePath, outputPath) {
    const optimizer = new ImageOptimizer({
        quality: 75,
        maxWidth: 1200,
        maxHeight: 800,
        format: 'webp',
        preserveOriginal: true
    });
    return optimizer.optimizeImage(imagePath, outputPath);
}
export async function createThumbnail(imagePath, outputPath) {
    const optimizer = new ImageOptimizer({
        quality: 70,
        maxWidth: 300,
        maxHeight: 300,
        format: 'webp',
        preserveOriginal: true
    });
    return optimizer.optimizeImage(imagePath, outputPath);
}
export async function optimizeForMobile(imagePath, outputPath) {
    const optimizer = new ImageOptimizer({
        quality: 65,
        maxWidth: 800,
        maxHeight: 600,
        format: 'webp',
        preserveOriginal: true
    });
    return optimizer.optimizeImage(imagePath, outputPath);
}
