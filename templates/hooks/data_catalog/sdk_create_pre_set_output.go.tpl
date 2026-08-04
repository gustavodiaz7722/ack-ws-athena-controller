	// CreateDataCatalog returns a nil DataCatalog body for non-FEDERATED
	// catalog types (LAMBDA, HIVE, GLUE). Guard against nil dereference in the
	// generated set-output block and preserve the desired Spec — the readOne
	// path reads authoritative state from GetDataCatalog on the next reconcile.
	if resp.DataCatalog == nil {
		rm.setStatusDefaults(ko)
		return &resource{ko}, nil
	}
