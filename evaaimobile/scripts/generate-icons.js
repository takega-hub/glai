const { Jimp } = require('jimp');
const path = require('path');
const fs = require('fs');

const SOURCE_ICON = path.join(__dirname, '../android/logo.png');
const RES_PATH = path.join(__dirname, '../android/app/src/main/res');

const SIZES = [
  { name: 'mipmap-mdpi', size: 48 },
  { name: 'mipmap-hdpi', size: 72 },
  { name: 'mipmap-xhdpi', size: 96 },
  { name: 'mipmap-xxhdpi', size: 144 },
  { name: 'mipmap-xxxhdpi', size: 192 },
];

async function generateIcons() {
  try {
    console.log('Reading source icon:', SOURCE_ICON);
    const image = await Jimp.read(SOURCE_ICON);

    for (const config of SIZES) {
      const targetDir = path.join(RES_PATH, config.name);

      if (!fs.existsSync(targetDir)) {
        fs.mkdirSync(targetDir, { recursive: true });
      }

      // 1. Generate standard square icon
      const squareIcon = image.clone().resize({ w: config.size, h: config.size });
      await squareIcon.write(path.join(targetDir, 'ic_launcher.png'));
      console.log(`Generated: ${config.name}/ic_launcher.png (${config.size}x${config.size})`);

      // 2. Generate round icon (circle)
      const roundIcon = image.clone().resize({ w: config.size, h: config.size });
      roundIcon.circle();
      await roundIcon.write(path.join(targetDir, 'ic_launcher_round.png'));
      console.log(`Generated: ${config.name}/ic_launcher_round.png (${config.size}x${config.size})`);
    }

    console.log('\nSUCCESS: All icons generated successfully for GL AI!');
  } catch (error) {
    console.error('Error generating icons:', error);
  }
}

generateIcons();
