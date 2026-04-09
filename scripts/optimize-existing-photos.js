#!/usr/bin/env node

import { ImageOptimizer } from '../dist/imageOptimizer.js';
import { promises as fs } from 'fs';
import path from 'path';

async function main() {
  console.log(`
🚀 Photo Optimization Tool for Existing Files
📁 Target: /opt/EVA_AI/uploads
  `);

  try {
    const uploadsDir = '/opt/EVA_AI/uploads';
    
    // Check if directory exists
    try {
      await fs.access(uploadsDir);
    } catch {
      console.error('❌ Uploads directory not found:', uploadsDir);
      process.exit(1);
    }

    console.log('📊 Analyzing existing photos...');
    
    // Find all image files
    const imageFiles = [];
    const supportedExtensions = ['.png', '.jpg', '.jpeg', '.webp'];
    
    async function findImages(dir) {
      const entries = await fs.readdir(dir, { withFileTypes: true });
      
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        
        if (entry.isDirectory()) {
          await findImages(fullPath);
        } else if (entry.isFile()) {
          const ext = path.extname(entry.name).toLowerCase();
          if (supportedExtensions.includes(ext)) {
            // Skip already optimized files
            if (!entry.name.includes('_optimized') && 
                !entry.name.includes('_web.') && 
                !entry.name.includes('_thumbnail.')) {
              imageFiles.push(fullPath);
            }
          }
        }
      }
    }
    
    await findImages(uploadsDir);
    
    if (imageFiles.length === 0) {
      console.log('✅ No images need optimization (all already optimized)');
      return;
    }

    console.log(`📸 Found ${imageFiles.length} images to optimize`);
    
    // Calculate current total size
    let totalOriginalSize = 0;
    for (const file of imageFiles) {
      const stats = await fs.stat(file);
      totalOriginalSize += stats.size;
    }
    
    console.log(`📏 Current total size: ${(totalOriginalSize / 1024 / 1024).toFixed(2)} MB`);
    
    // Configure optimizer for web use
    const optimizer = new ImageOptimizer({
      quality: 75,
      maxWidth: 1200,
      maxHeight: 800,
      format: 'webp',
      preserveOriginal: true // Keep originals safe
    });
    
    console.log('\n⚙️  Optimization settings:');
    console.log('   • Quality: 75%');
    console.log('   • Max dimensions: 1200x800px');
    console.log('   • Format: WebP');
    console.log('   • Preserving originals: Yes');
    
    console.log('\n🔄 Starting optimization...\n');
    
    let totalOptimizedSize = 0;
    let successfulOptimizations = 0;
    const results = [];
    
    for (let i = 0; i < imageFiles.length; i++) {
      const file = imageFiles[i];
      const fileName = path.basename(file);
      
      try {
        console.log(`[${i + 1}/${imageFiles.length}] Processing: ${fileName}`);
        
        const result = await optimizer.optimizeImage(file);
        
        results.push({
          file: fileName,
          originalSize: result.originalSize,
          optimizedSize: result.optimizedSize,
          savedPercentage: result.savedPercentage,
          outputPath: result.outputPath
        });
        
        totalOptimizedSize += result.optimizedSize;
        successfulOptimizations++;
        
        console.log(`   ✅ Saved ${result.savedPercentage.toFixed(1)}% (${(result.originalSize/1024).toFixed(1)}KB → ${(result.optimizedSize/1024).toFixed(1)}KB)`);
        
      } catch (error) {
        console.log(`   ❌ Failed: ${error.message}`);
      }
    }
    
    // Summary
    const totalSavedBytes = totalOriginalSize - totalOptimizedSize;
    const averageSavings = results.length > 0 
      ? results.reduce((sum, r) => sum + r.savedPercentage, 0) / results.length 
      : 0;
    
    console.log(`
✅ Optimization Complete!

📊 Summary:
   • Files processed: ${successfulOptimizations}/${imageFiles.length}
   • Total space saved: ${(totalSavedBytes / 1024 / 1024).toFixed(2)} MB
   • Average savings: ${averageSavings.toFixed(1)}%
   • Original total size: ${(totalOriginalSize / 1024 / 1024).toFixed(2)} MB
   • Optimized total size: ${(totalOptimizedSize / 1024 / 1024).toFixed(2)} MB

💡 Next Steps:
   1. Test the optimized images in your application
   2. Update your image URLs to use the optimized versions
   3. Consider implementing the upload optimizer for new files
   4. Monitor your application's loading performance

🗂️  File Structure:
   • Original files: Preserved with original names
   • Optimized files: Added with '_optimized.webp' suffix
   • Web versions: Available for immediate use
    `);

    // Show top 5 biggest savings
    if (results.length > 0) {
      const topSavings = results
        .sort((a, b) => b.savedPercentage - a.savedPercentage)
        .slice(0, 5);
      
      console.log('\n🏆 Top 5 Space Savers:');
      topSavings.forEach((result, index) => {
        console.log(`   ${index + 1}. ${result.file}: ${result.savedPercentage.toFixed(1)}% saved`);
      });
    }

  } catch (error) {
    console.error(`\n❌ Fatal error: ${error.message}`);
    process.exit(1);
  }
}

// Handle unhandled promise rejections
process.on('unhandledRejection', (error) => {
  console.error('❌ Unhandled promise rejection:', error);
  process.exit(1);
});

main().catch(error => {
  console.error('❌ Fatal error:', error);
  process.exit(1);
});