	// UpdateWorkGroup accepts a WorkGroupConfigurationUpdates shape rather than
	// the WorkGroupConfiguration shape used on create. Because the field names
	// differ, the generated newUpdateRequestPayload does not map
	// Spec.Configuration into the update request, so managed query results
	// changes would otherwise be silently dropped. Wire them through manually.
	if delta.DifferentAt("Spec.Configuration.ManagedQueryResultsConfiguration") &&
		desired.ko.Spec.Configuration != nil {
		mqrc := desired.ko.Spec.Configuration.ManagedQueryResultsConfiguration
		mqrcUpdates := &svcsdktypes.ManagedQueryResultsConfigurationUpdates{}
		if mqrc != nil {
			if mqrc.Enabled != nil {
				mqrcUpdates.Enabled = mqrc.Enabled
			}
			if mqrc.EncryptionConfiguration != nil &&
				mqrc.EncryptionConfiguration.KMSKey != nil {
				mqrcUpdates.EncryptionConfiguration = &svcsdktypes.ManagedQueryResultsEncryptionConfiguration{
					KmsKey: mqrc.EncryptionConfiguration.KMSKey,
				}
			}
		}
		if input.ConfigurationUpdates == nil {
			input.ConfigurationUpdates = &svcsdktypes.WorkGroupConfigurationUpdates{}
		}
		input.ConfigurationUpdates.ManagedQueryResultsConfigurationUpdates = mqrcUpdates
	}
