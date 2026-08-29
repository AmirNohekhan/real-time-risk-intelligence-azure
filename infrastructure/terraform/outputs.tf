output "resource_group" { value = azurerm_resource_group.this.name }
output "ml_workspace" { value = azurerm_machine_learning_workspace.this.name }
output "event_hub_namespace" { value = azurerm_eventhub_namespace.this.name }
output "service_bus_namespace" { value = azurerm_servicebus_namespace.this.name }
output "storage_account" { value = azurerm_storage_account.this.name }

