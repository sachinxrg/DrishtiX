db.alert_config.updateOne({config_key: 'ingestion_enabled'}, {$set: {config_value: 'true'}}, {upsert: true});
db.alert_config.updateOne({config_key: 'fbi_api_key'}, {$set: {config_value: 'YOUR_API_KEY_HERE'}}, {upsert: true});
