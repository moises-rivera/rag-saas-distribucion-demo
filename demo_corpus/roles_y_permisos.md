# Nébula Distribuciones — Roles y permisos

> Contenido ficticio creado únicamente para demostración del RAG.

Nébula Distribuciones utiliza cuatro perfiles de ejemplo para separar tareas operativas, administrativas y de consulta.

## Leyenda

- **P:** permitido.
- **L:** permitido con límite o alcance.
- **A:** requiere aprobación.
- **N:** no permitido.

## Matriz de permisos

| Acción | Admin | Vendedor | Cajero | Consulta |
|---|---|---|---|---|
| Ajustar inventario | P | A | N | N |
| Registrar pedido | P | P | L | N |
| Anular comprobante | P | N | A | N |

## Criterios operativos

- El perfil Admin administra la configuración general de esta empresa ficticia.
- El perfil Vendedor registra pedidos y solicita aprobación cuando una operación afecta existencias.
- El perfil Cajero trabaja con cobros y tiene un alcance limitado fuera de caja.
- El perfil Consulta sólo visualiza información autorizada.
