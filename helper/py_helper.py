def table_exists(db, table_name):
    query = "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name=%s);"
    result = db.execute_query(query, (table_name,))
    return result and result[0][0]

def create_domain_table(db, domain, feature_names):
    # Sanitize feature names for column names
    columns = ', '.join([f'"{feat.replace(" ", "_").lower()}" TEXT' for feat in feature_names])
    query = f'CREATE TABLE "{domain}" (id SERIAL PRIMARY KEY, {columns});'
    db.execute_query(query)