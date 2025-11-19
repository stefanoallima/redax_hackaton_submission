
  # test_report.py
  from pii_detector_integrated import IntegratedPIIDetector

  # Test document
  text = """
  INTRODUZIONE
  Il presente documento tratta...

  CAPITOLO PRIMO

  Il signor Mario Rossi, nato a Roma il 15/03/1985,
  codice fiscale RSSMRA85C15H501X, residente in
  Via Giuseppe Garibaldi 123, Milano (MI),
  telefono 02-12345678, email mario.rossi@example.com

  Il ricorso è presentato contro INPS presso il
  Tribunale di Milano. Secondo Francesco Carnelutti...
  """

  # Run detection
  detector = IntegratedPIIDetector()
  result = detector.detect_pii(text, depth="balanced")

  # Print report
  print("\n" + "="*70)
  print("PII DETECTION REPORT")
  print("="*70)

  print(f"\n📊 SUMMARY:")
  print(f"  Total entities detected: {len(result['entities'])}")
  print(f"  Processing time: {result['performance']['total_time_ms']:.2f}ms")    
  print(f"  Document type: {result['metadata'].get('document_type', 'N/A')}")    

  print(f"\n🔍 OPTIMIZATIONS:")
  print(f"  Pre-filtering: {result['metadata']['prefilter_applied']}")
  if result['metadata']['prefilter_applied']:
      stats = result['metadata']['prefilter_stats']
      print(f"    - Skipped {stats['skipped_lines']} lines
  ({stats['skip_percentage']:.1f}%)")
  print(f"  Italian context filtered:
  {result['metadata']['italian_context_filtered']} entities")

  print(f"\n✅ DETECTED ENTITIES:")
  for i, entity in enumerate(result['entities'], 1):
      print(f"  {i}. {entity['entity_type']}: \"{entity['text']}\"")
      print(f"     Score: {entity['score']:.2f}, Source: {entity['source']}")    

  print(f"\n📈 STATISTICS:")
  stats = result['stats']
  print(f"  Average confidence: {stats['avg_confidence']:.3f}")
  print(f"  By type:")
  for entity_type, count in sorted(stats['by_type'].items()):
      print(f"    - {entity_type}: {count}")

  print("\n" + "="*70)