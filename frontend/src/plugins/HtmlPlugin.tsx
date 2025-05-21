import { useEffect } from "react";
import { useLexicalComposerContext } from "@lexical/react/LexicalComposerContext";
import { $getRoot, $insertNodes } from "lexical"; // Added $insertNodes

type HtmlPluginProps = {
  html: string;
};

export function HtmlPlugin({ html }: HtmlPluginProps) {
  const [editor] = useLexicalComposerContext();

  useEffect(() => {
    // This effect runs when `html` or `editor` instance changes.
    (async () => {
      try {
        const { $generateNodesFromDOM } = await import("@lexical/html");

        editor.update(() => {
          const root = $getRoot();
          root.clear(); // Always clear the editor content first.
          
          // Ensure selection is at the start of the root after clearing.
          // This helps $insertNodes to correctly place content in the empty root.
          root.selectStart();


          // Only parse and append nodes if html is a non-empty, non-whitespace string.
          if (html && html.trim() !== "") {
            const parser = new DOMParser();
            const dom = parser.parseFromString(html, "text/html");
            const nodes = $generateNodesFromDOM(editor, dom);
            
            if (nodes.length > 0) {
              // Use $insertNodes to correctly insert the generated nodes.
              // This utility handles wrapping TextNodes in ParagraphNodes if necessary.
              $insertNodes(nodes);
            }
          }
          // If html is empty or just whitespace, the editor will remain cleared.
        });
      } catch (error) {
        console.error("Error setting HTML in editor:", error);
      }
    })();
  }, [html, editor]); // Dependencies: re-run if html content or editor instance changes.

  return null;
}
