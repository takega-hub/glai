#!/usr/bin/env node

import { ImageOptimizer } from '../src/utils/imageOptimizer.js';
import { promises as fs } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    console.log(`
📸 Photo Optimizer CLI

Usage: node optimize-photos.js [directory] [options]

Options:
  --quality <number>     Image quality (1-100, default: 80)
  --max-width <number>   Maximum width in pixels (default: 1920)
  --max-height <number>  Maximum height in pixels (default: 1080)
  --format <format>      Output format: webp, jpeg, png (default: webp)
  --replace             Replace original files (DANGEROUS!)
  --help                Show this help message

Examples:
  node optimize-photos.js /opt/EVA_AI/uploads
  node optimize-photos.js ./images --quality 75 --format webp
  node optimize-photos.js ./photos --max-width 1200 --max-height 800

Presets:
  --web                 Optimize for web (quality: 75, max-width: 1200)
  --mobile              Optimize for mobile (quality: 65, max-width: 800)
  --thumbnail           Create thumbnails (quality: 70, max-width: 300)
    `);
    return;
  }

  let directory = args[0];
  let options = {};

  // Parse command line arguments
  for (let i = 1; i < args.length; i++) {
    switch (args[i]) {
      case '--quality':
        options.quality = parseInt(args[++i]);
        break;
      case '--max-width':
        options.maxWidth = parseInt(args[++i]);
        break;
      case '--max-height':
        options.maxHeight = parseInt(args[++i]);
        break;
      case '--format':
        options.format = args[++i];
        break;
      case '--replace':
        options.preserveOriginal = false;
        break;
      case '--web':
        options = { quality: 75, maxWidth: 1200, maxHeight: 800, format: 'webp' };
        break;
      case '--mobile':
        options = { quality: 65, maxWidth: 800, maxHeight: 600, format: 'webp' };
        break;
      case '--thumbnail':
        options = { quality: 70, maxWidth: 300, maxHeight: 300, format: 'webp' };
        break;
      case '--help':
        console.log('Use --help to see available options');
        return;
    }
  }

  // Ensure directory path is absolute
  if (!path.isAbsolute(directory)) {
    directory = path.resolve(process.cwd(), directory);
  }

  console.log(`
🚀 Starting photo optimization...
📁 Directory: ${directory}
⚙️  Options: ${JSON.stringify(options, null, 2)}
  `);

  try {
    // Check if directory exists
    await fs.access(directory);
    
    const optimizer = new ImageOptimizer(options);
    const result = await optimizer.optimizeDirectory(directory, options);

    console.log(`
✅ Optimization Complete!

📊 Statistics:
   • Total files found: ${result.totalFiles}
   • Successfully optimized: ${result.optimizedFiles}
   • Total space saved: ${(result.totalSaved / 1024 / 1024).toFixed(2)} MB
   • Average savings: ${result.results.length > 0 
     ? (result.results.reduce((sum, r) => sum + r.savedPercentage, 0) / result.results.length).toFixed(1)
     : 0}%

💡 Tips for future uploads:
   • Use the optimization utility in your upload handler
   • Consider creating multiple sizes (thumbnail, web, full)
   • Set appropriate quality settings for your use case
    `);

    // Show detailed results if less than 10 files
    if (result.results.length <= 10) {
      console.log('\n📄 Detailed Results:');
      result.results.forEach(r => {
        console.log(`   • ${r.file}: ${(r.originalSize/1024).toFixed(1)}KB → ${(r.optimizedSize/1024).toFixed(1)}KB (${r.savedPercentage.toFixed(1)}% saved)`);
      });
    }

  } catch (error) {
    console.error(`❌ Error: ${error.message}`);
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