// frontend/src/plugins/ImagePlugin.tsx
import { useLexicalComposerContext } from "@lexical/react/LexicalComposerContext";
import { useEffect } from "react";
import { $createImageNode } from "../nodes/ImageNode";
import { $insertNodes } from "lexical";

export function ImagePlugin() {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    const handlePaste = async (event: ClipboardEvent) => {
      const items = event.clipboardData?.items;
      if (!items) return;

      // Check for HTML content and if it's a table
      if (event.clipboardData && event.clipboardData.types.includes("text/html")) {
        const html = event.clipboardData.getData("text/html");
        // A simple check for table tags. This might need to be more robust
        // depending on the variety of HTML from Excel.
        if (html.includes("<table") || html.includes("<TABLE")) {
          return; // It's a table, don't process as an image
        }
      }

      for (const item of items) {
        if (item.type.startsWith("image/")) {
          const file = item.getAsFile();
          if (!file) continue;

          const formData = new FormData();
          formData.append("file", file);

          try {
            const res = await fetch("/api/upload-image", {
              method: "POST",
              body: formData,
            });
            const data = await res.json();
            const url = data.url;

            editor.update(() => {
              const imageNode = $createImageNode({
                src: url,
                altText: file.name || "Pasted image",
                maxWidth: 500, // You can make this configurable
              });
              $insertNodes([imageNode]);
            });
          } catch (err) {
            console.error("Image upload failed", err);
          }
        }
      }
    };

    document.addEventListener("paste", handlePaste);
    return () => document.removeEventListener("paste", handlePaste);
  }, [editor]);

  return null;
}
