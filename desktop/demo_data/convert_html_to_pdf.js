/**
 * Convert HTML to PDF using Electron
 * Run from desktop directory: node demo_data/convert_html_to_pdf.js
 */
const fs = require('fs');
const path = require('path');
const { app, BrowserWindow } = require('electron');

const demoDir = __dirname;
const htmlFiles = fs.readdirSync(demoDir)
  .filter(f => f.endsWith('_UNREDACTED.html'))
  .sort();

console.log(`Found ${htmlFiles.length} HTML files to convert`);

let currentIndex = 0;

async function convertNext() {
  if (currentIndex >= htmlFiles.length) {
    console.log('\n✓ All files converted!');
    app.quit();
    return;
  }

  const htmlFile = htmlFiles[currentIndex];
  const pdfFile = htmlFile.replace('.html', '.pdf');
  const htmlPath = path.join(demoDir, htmlFile);
  const pdfPath = path.join(demoDir, pdfFile);

  console.log(`Converting ${htmlFile}...`);

  const win = new BrowserWindow({ show: false });

  await win.loadFile(htmlPath);

  const pdfData = await win.webContents.printToPDF({
    pageSize: 'Letter',
    printBackground: true,
    margins: {
      top: 0.5,
      bottom: 0.5,
      left: 0.5,
      right: 0.5
    }
  });

  fs.writeFileSync(pdfPath, pdfData);
  console.log(`✓ Created ${pdfFile}`);

  win.close();
  currentIndex++;

  // Convert next
  setTimeout(convertNext, 100);
}

app.whenReady().then(() => {
  console.log('Starting HTML to PDF conversion...\n');
  convertNext();
});

app.on('window-all-closed', () => {
  // Keep running until we're done
});
