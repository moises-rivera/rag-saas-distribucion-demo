# Nébula Distribuciones — Inventario de demostración

> Contenido ficticio creado únicamente para demostración del RAG.

El módulo ficticio de inventario registra entradas, salidas y ajustes. Cada movimiento conserva fecha, producto, cantidad, motivo y responsable.

## Flujo de ajuste

1. Buscar el producto por nombre o código.
2. Comparar la cantidad física con la cantidad registrada.
3. Indicar la diferencia y seleccionar un motivo.
4. Confirmar la operación si el rol dispone del permiso correspondiente.

## Motivos admitidos

- Conteo físico.
- Producto dañado.
- Corrección de recepción.
- Regularización de despacho.

## Productos de ejemplo

| Código | Producto | Unidad | Stock mínimo |
|---|---|---|---:|
| DEM-101 | Bebida Boreal | Caja | 12 |
| DEM-205 | Galleta Cometa | Paquete | 30 |
| DEM-310 | Conserva Aurora | Unidad | 24 |

Los nombres, códigos y cantidades de esta tabla son inventados y no representan datos comerciales reales.
