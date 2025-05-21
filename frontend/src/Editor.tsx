import { useState } from "react";
import { LexicalComposer } from "@lexical/react/LexicalComposer";
import { RichTextPlugin } from "@lexical/react/LexicalRichTextPlugin";
import { ContentEditable } from "@lexical/react/LexicalContentEditable";
import { HistoryPlugin } from "@lexical/react/LexicalHistoryPlugin";
import { OnChangePlugin } from "@lexical/react/LexicalOnChangePlugin";
import { AutoFocusPlugin } from "@lexical/react/LexicalAutoFocusPlugin";
import { LexicalErrorBoundary } from "@lexical/react/LexicalErrorBoundary";
import { TablePlugin } from "@lexical/react/LexicalTablePlugin";

import {
  TableCellNode,
  TableNode,
  TableRowNode,
} from "@lexical/table";

import { type LexicalEditor } from "lexical";
import { HtmlPlugin } from "./plugins/HtmlPlugin";
import { ImagePlugin } from "./plugins/ImagePlugin";
import { ImageNode } from "./nodes/ImageNode";
import axios from "axios";

import ExampleTheme from "./ExampleTheme.ts";
import ToolbarPlugin from "./plugins/ToolbarPlugin";

import "highlight.js/styles/github.css";
import "./styles.css";

const editorConfig = {
  namespace: "MyEditor",
  onError(error: Error) {
    throw error;
  },
  nodes: [ImageNode, TableNode, TableCellNode, TableRowNode],
  theme: ExampleTheme,
};

function Placeholder() {
  return <div style={{ color: "rgb(156 163 175)" }}>Enter some text...</div>;
}

export default function Editor() {
  const [editor, setEditor] = useState<LexicalEditor | null>(null);
  const [initialHtml, setInitialHtml] = useState<string>("");

  const handleSave = async () => {
    if (!editor) return;
    const { $generateHtmlFromNodes } = await import("@lexical/html");
    let html = "";
    editor.update(() => {
      html = $generateHtmlFromNodes(editor, null);
    });
    await axios.post("/api/save", { html });
    alert("Saved");
  };

  const handleLoad = async () => {
    const res = await axios.get("/api/load");
    setInitialHtml(res.data.html || "");
  };

  return (
    <div>
      <LexicalComposer initialConfig={editorConfig}>
        <div className="editor-container">
          <ToolbarPlugin />
          <div className="editor-inner">
            <RichTextPlugin
              contentEditable={<ContentEditable className="editor-input" />}
              placeholder={<Placeholder />}
              ErrorBoundary={LexicalErrorBoundary}
            />
            <HistoryPlugin />
            <AutoFocusPlugin />
            <TablePlugin />
            <OnChangePlugin
              onChange={(_editorState, editorInstance) => {
                setEditor(editorInstance);
              }}
            />
            <HtmlPlugin html={initialHtml} />
            <ImagePlugin />
          </div>
        </div>
      </LexicalComposer>

      <div style={{ marginTop: "1rem" }}>
        <button
          onClick={handleSave}
          style={{
            backgroundColor: "rgb(59 130 246)",
            color: "white",
            paddingLeft: "1rem",
            paddingRight: "1rem",
            paddingTop: "0.5rem",
            paddingBottom: "0.5rem",
            borderRadius: "0.25rem",
          }}
        >
          Save
        </button>
        <button
          onClick={handleLoad}
          style={{
            backgroundColor: "rgb(34 197 94)",
            color: "white",
            paddingLeft: "1rem",
            paddingRight: "1rem",
            paddingTop: "0.5rem",
            paddingBottom: "0.5rem",
            borderRadius: "0.25rem",
            marginLeft: "0.5rem",
          }}
        >
          Load
        </button>
      </div>
    </div>
  );
}
