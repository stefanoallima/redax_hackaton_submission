/**
 * Electron Builder Configuration for Windows Installer
 * Bundles Python + AI models (~1.7GB total)
 */

module.exports = {
  appId: 'com.redaxai.redact',
  productName: 'Redax AI',
  
  directories: {
    output: 'dist/installers',
    buildResources: 'assets'
  },
  
  files: [
    'dist/**/*',
    'src/python/**/*',
    '!src/python/venv/**/*',
    '!src/python/__pycache__/**/*',
    '!**/*.pyc'
  ],
  
  extraResources: [
    {
      from: 'src/python',
      to: 'python',
      filter: ['**/*', '!venv/**/*', '!__pycache__/**/*']
    },
    // Include AI models if pre-downloaded
    // {
    //   from: 'models',
    //   to: 'models'
    // }
  ],
  
  win: {
    target: [
      {
        target: 'nsis',
        arch: ['x64']
      }
    ],
    icon: 'assets/icon.ico',
    publisherName: 'redaxai.com',
    
    // Code signing (requires certificate)
    // certificateFile: 'path/to/certificate.pfx',
    // certificatePassword: process.env.CERT_PASSWORD,
    
    // File associations
    fileAssociations: [
      {
        ext: 'pdf',
        name: 'PDF Document',
        role: 'Editor'
      }
    ]
  },
  
  nsis: {
    oneClick: false,
    allowToChangeInstallationDirectory: true,
    allowElevation: true,
    createDesktopShortcut: true,
    createStartMenuShortcut: true,
    
    installerIcon: 'assets/icon.ico',
    uninstallerIcon: 'assets/icon.ico',
    
    // License agreement
    license: 'LICENSE.txt',
    
    // Install Python dependencies during installation
    include: 'installer-script.nsh',
    
    // Compression
    compression: 'maximum'
  },
  
  mac: {
    target: ['dmg'],
    icon: 'assets/icon.icns',
    category: 'public.app-category.productivity',
    hardenedRuntime: true,
    gatekeeperAssess: false,
    entitlements: 'build/entitlements.mac.plist',
    entitlementsInherit: 'build/entitlements.mac.plist'
  },
  
  dmg: {
    contents: [
      {
        x: 130,
        y: 220
      },
      {
        x: 410,
        y: 220,
        type: 'link',
        path: '/Applications'
      }
    ]
  },
  
  linux: {
    target: ['AppImage'],
    category: 'Office',
    icon: 'assets/icon.png'
  },
  
  // Auto-updater configuration
  publish: {
    provider: 'github',
    owner: 'your-username',
    repo: 'redaxai',
    private: false
  },
  
  // Artifact naming
  artifactName: '${productName}-${version}-${os}-${arch}.${ext}'
}
