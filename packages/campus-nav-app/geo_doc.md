# How to Create a Proper GeoJSON for Traverse

To upload your own map into **Traverse**, there are a few important rules to follow. Please read carefully to ensure your map processes correctly.

## Recommended Tool
We recommend using [geojson.io](https://geojson.io) for creating and editing your GeoJSON files. It’s simple and easy to use!

## Drawing Your Map
- **Polygons**:  
  Use the **Polygon tool** to draw each building, obstacle, or area you want to map.

- **Lines**:  
  Use the **Line tool** to draw hallways, walkways, or shortcuts you want users to traverse through.

- **Points (Entrances)**:  
  Use the **Point tool** to mark each entrance.  
  ➔ *Important:* Points must be placed **inside** the corresponding polygon (building) they belong to.

## Naming Requirements
- Every **polygon** must have a property called `"name"` set to the **building's name**.
- Points (entrances) will be automatically processed and **numbered clockwise** like an analog clock:  
  - Lower numbers (e.g., 1, 2) will be near the **top-right** of the building.
  - Higher numbers (e.g., 10, 11) will be near the **top-left**.

## Setting Bounds
Once you are finished placing all your polygons, lines, and points:
- Use the **Square (Rectangle) tool** to draw a box around your entire map.  
  ➔ This defines the bounds of your navigable area.

## Helpful Tip
Refer to the **provided example image** as a guide while creating your map!

## Picture For Refrence
![Alt Text](path-to-your-image.png)