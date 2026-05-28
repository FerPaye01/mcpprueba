---
name: osinergmin-theming
description: Applies Osinergmin branding (colors and logo) to Chainlit applications. Use this skill when a user wants to customize their chatbot with the official visual identity of Osinergmin (Peru).
---

# Osinergmin Theming Skill

This skill provides the resources and instructions to theme a Chainlit application with Osinergmin's visual identity.

## Visual Identity Details
- **Primary Blue:** `RGB R 0 G 57 B 170` 
- **Secondary Light Blue:** `RGB R 3 G 169 B 244` 
- **Yellow:** `RGB R 251 G 225 B 34`
- **Green:** `RGB R 53 G 204 B 41`
- **Sky blue:** `RGB R 210 G 247 B 252`
- **Orange:** `RGB R 246 G 162 B 41`
- **White:** `RGB R 242 G 242 B 242`
- **Mostaza:** `RGB R 191 G 171 B 73`


- **Logo:** Official Osinergmin logo (requires `public/logo.png`)

## Workflow

1. **Create Public Directory**: Ensure there is a `public` folder in the root of the Chainlit project.
2. **Deploy Assets**: 
   - Copy `assets/custom.css` to `public/osinergmin.css`.
   - Place the Osinergmin logo as `public/logo.png`.
3. **Update Configuration**: Modify `.chainlit/config.toml` to use these assets.

### Recommended config.toml updates:

```toml
[UI]
name = "Asistente Osinergmin"
logo_file_url = "/public/logo.png"
custom_css = "/public/osinergmin.css"
```

## References
- See `references/branding.md` for more technical details on the color palette.
