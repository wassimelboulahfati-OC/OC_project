import pandas as pd
df = pd.read_parquet('output/tickets_enriched')
print("=== APERÇU DES TICKETS ENRICHIS ===")
print(df.head(10).to_string())
print(f"\nTotal tickets traités : {len(df)}")
print("\n=== RÉPARTITION PAR ÉQUIPE ===")
print(df['equipe_support'].value_counts())
