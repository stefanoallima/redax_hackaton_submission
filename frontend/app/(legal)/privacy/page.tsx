/**
 * Privacy Policy page
 */
export default function PrivacyPolicy() {
  return (
    <main className="container mx-auto px-4 py-12 max-w-4xl">
      <h1 className="text-4xl font-bold mb-8">Privacy Policy</h1>
      
      <div className="prose prose-lg">
        <p className="text-gray-600 mb-4">
          <strong>Last Updated:</strong> January 2025
        </p>
        
        <h2>1. Introduction</h2>
        <p>
          CodiceCivile.ai ("we", "our", or "us") is committed to protecting your privacy. 
          This Privacy Policy explains how we collect, use, disclose, and safeguard your 
          information when you use our platform.
        </p>
        
        <h2>2. Information We Collect</h2>
        <h3>2.1 Personal Information</h3>
        <ul>
          <li>Name and email address (registration)</li>
          <li>Payment information (processed by Stripe)</li>
          <li>Usage data and analytics</li>
        </ul>
        
        <h3>2.2 Desktop App - Privacy First</h3>
        <p>
          <strong>Important:</strong> The CodiceCivile Redact desktop application processes 
          all documents <strong>100% offline</strong> on your local machine. We never receive, 
          store, or transmit your original documents or any personally identifiable information 
          from those documents.
        </p>
        
        <h2>3. How We Use Your Information</h2>
        <ul>
          <li>Provide and maintain our services</li>
          <li>Process payments and subscriptions</li>
          <li>Send important service updates</li>
          <li>Improve our platform</li>
        </ul>
        
        <h2>4. Data Storage and Security</h2>
        <p>
          We implement appropriate technical and organizational measures to protect your 
          personal data, including:
        </p>
        <ul>
          <li>Encryption at rest (AES-256) and in transit (TLS 1.3)</li>
          <li>Regular security audits</li>
          <li>Access controls and authentication</li>
        </ul>
        
        <h2>5. Your GDPR Rights</h2>
        <p>
          Under the General Data Protection Regulation (GDPR), you have the following rights:
        </p>
        <ul>
          <li><strong>Right to Access:</strong> Export all your data</li>
          <li><strong>Right to Erasure:</strong> Delete your account and all data</li>
          <li><strong>Right to Portability:</strong> Receive your data in JSON format</li>
          <li><strong>Right to Rectification:</strong> Update your information</li>
        </ul>
        
        <p>
          To exercise these rights, visit your account settings or contact us at 
          privacy@codicecivile.ai
        </p>
        
        <h2>6. Data Retention</h2>
        <p>
          We retain your personal data only as long as necessary to provide our services 
          or as required by law. You can request deletion at any time.
        </p>
        
        <h2>7. Third-Party Services</h2>
        <ul>
          <li><strong>Stripe:</strong> Payment processing</li>
          <li><strong>Anthropic:</strong> AI chat functionality</li>
          <li><strong>DigitalOcean:</strong> Infrastructure hosting</li>
        </ul>
        
        <h2>8. Cookies</h2>
        <p>
          We use essential cookies for authentication. You can control cookie preferences 
          in your browser settings.
        </p>
        
        <h2>9. Changes to This Policy</h2>
        <p>
          We may update this Privacy Policy from time to time. We will notify you of any 
          changes by email or through the platform.
        </p>
        
        <h2>10. Contact Us</h2>
        <p>
          If you have questions about this Privacy Policy, please contact us at:
        </p>
        <p>
          Email: privacy@codicecivile.ai<br />
          Address: [Your Address]
        </p>
      </div>
    </main>
  )
}
