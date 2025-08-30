// App.tsx
import { useState } from "react";
import {
  Image as RNImage,
  View,
  Text,
  Pressable,
  StyleSheet,
  Platform,
  Modal,
  ActivityIndicator,
} from "react-native";
import * as ImagePicker from "expo-image-picker";

function getBaseUrl() {
  return Platform.OS === "android" ? "http://10.0.2.2:8080" : "http://localhost:8080";
}

type Screen = "idle" | "loading" | "result";

export default function App() {
  const [img, setImg] = useState<{ uri: string; type?: string; w?: number; h?: number } | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const [screen, setScreen] = useState<Screen>("idle");

  async function pick() {
    setErr(null);
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== "granted") return setErr("Permission denied");
    const res = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.9,
      allowsMultipleSelection: false,
    });
    if (!res.canceled) {
      const a = res.assets[0];
      setImg({
        uri: a.uri,
        type: a.mimeType ?? "image/jpeg",
        w: a.width ?? 0,
        h: a.height ?? 0,
      });
      setResult(null);
      setScreen("idle"); // back to idle view with buttons
    }
  }

  function extFromMime(m?: string) {
    if (!m) return "bin";
    if (m.includes("jpeg") || m.includes("jpg")) return "jpg";
    if (m.includes("png")) return "png";
    if (m.includes("webp")) return "webp";
    if (m.includes("heic")) return "heic";
    return "bin";
  }

  async function upload() {
    if (!img) return;
    setBusy(true);
    setErr(null);
    setScreen("loading"); // show loading page immediately

    try {
      const url = `${getBaseUrl()}/analyze/image`;
      const fd = new FormData();

      if (Platform.OS === "web") {
        // Web: convert blob: URI to Blob/File
        const resp = await fetch(img.uri);
        const blob = await resp.blob();
        const mime = blob.type || img.type || "image/jpeg";
        const name = `upload.${extFromMime(mime)}`;
        fd.append("file", new File([blob], name, { type: mime }));
      } else {
        // Native: RN file object
        const mime = img.type || "image/jpeg";
        const name = `upload.${extFromMime(mime)}`;
        // @ts-ignore
        fd.append("file", { uri: img.uri, name, type: mime });
      }

      const r = await fetch(url, { method: "POST", body: fd });

      const text = await r.text();
      if (!r.ok) throw new Error(`HTTP ${r.status}: ${text}`);

      setResult(JSON.parse(text));
      setScreen("result");
    } catch (e: any) {
      setErr(String(e.message || e));
      setScreen("idle");
    } finally {
      setBusy(false);
    }
  }

  // ---- Render by screen ----
  if (screen === "loading") {
    return (
      <View style={styles.fullscreenCenter}>
        <ActivityIndicator size="large" />
        <Text style={{ marginTop: 12, fontWeight: "600" }}>Analyzing image…</Text>
      </View>
    );
  }

  if (screen === "result") {
    // Results page: show image + overlay boxes only
    return (
      <View style={{ padding: 16, gap: 12, flex: 1, justifyContent: "center" }}>
        <UploadBox imageUri={img?.uri || null} result={result} onPress={() => {}} showChangeStrip={false} />
        {err && <Text style={{ color: "red" }}>{err}</Text>}
      </View>
    );
  }

  // Idle (default) page: picker + analyze button
  return (
    <View style={{ padding: 16, gap: 12, flex: 1, justifyContent: "center" }}>
      <UploadBox imageUri={img?.uri || null} result={result} busy={busy} onPress={pick} />

      {img && (
        <Pressable
          onPress={upload}
          disabled={busy}
          style={[styles.uploadBtn, busy && { opacity: 0.6 }]}
          accessibilityRole="button"
        >
          <Text style={styles.uploadBtnText}>{busy ? "Uploading…" : "Analyze image"}</Text>
        </Pressable>
      )}

      {err && <Text style={{ color: "red" }}>{err}</Text>}
    </View>
  );
}

function UploadBox({ imageUri, result, onPress, busy, readOnly = false, showChangeStrip = true }: {   imageUri: string | null;
  result?: any;
  onPress: () => void;
  busy?: boolean;
  readOnly?: boolean;
  showChangeStrip?: boolean; }) {
  const [container, setContainer] = useState({ w: 0, h: 0 });
  const [natural, setNatural] = useState({ w: 0, h: 0 });
  const [selected, setSelected] = useState<any | null>(null);

  // ✅ When no image: whole box is a button to pick
  if (!imageUri) {
    return (
      <Pressable
        onPress={onPress}
        accessibilityRole="button"
        style={({ pressed }) => [
          styles.box,
          styles.boxEmpty,
          pressed && { opacity: 0.85 },
        ]}
      >
        <View style={styles.boxInner}>
          <Text style={styles.icon}>⬆️</Text>
          <Text style={styles.title}>Tap to upload</Text>
          <Text style={styles.subtitle}>PNG or JPG, up to ~10MB</Text>
        </View>
      </Pressable>
    );
  }

  // ✅ When image exists: use a plain View so parent can't steal touches
  return (
    <View
      style={[styles.box, styles.boxWithImage]}
      onLayout={(e) => {
        const { width, height } = e.nativeEvent.layout;
        setContainer({ w: width, h: height });
      }}
      collapsable={false}  // <- helps absolute overlays stay hittable
    >
      <RNImage
        source={{ uri: imageUri }}
        style={styles.boxImage}
        resizeMode="contain"
        pointerEvents="none"
        onLoad={(e) => {
          const src = (e?.nativeEvent as any)?.source; // iOS/Android provide this, web may not
          if (src?.width && src?.height) {
            setNatural((prev) => ({ w: src.width || prev.w, h: src.height || prev.h }));
            return;
          }
          // Fallback: ask RN for the intrinsic size (works on native & web)
          RNImage.getSize(
            imageUri,
            (w, h) => setNatural({ w, h }),
            () => {
              // optional: keep previous if getSize fails
              // setNatural(prev => prev)
            }
          );
        }}
      />


      {/* Overlays */}
      {result?.findings?.map((f: any, i: number) => {
        const [nx, ny, nw, nh] = f.bbox as number[];
        const iw = natural.w || container.w;
        const ih = natural.h || container.h;
        const scale = Math.min(container.w / (iw || 1), container.h / (ih || 1));
        const dispW = (iw || 0) * scale;
        const dispH = (ih || 0) * scale;
        const offsetX = (container.w - dispW) / 2;
        const offsetY = (container.h - dispH) / 2;

        const left = offsetX + nx * dispW;
        const top = offsetY + ny * dispH;
        const width = nw * dispW;
        const height = nh * dispH;

        const PADDING = 3;
        const rect = {
          left: left - PADDING,
          top: top - PADDING,
          width: width + PADDING * 2,
          height: height + PADDING * 2,
        };

        const boxStyle = {
          position: "absolute" as const,
          ...rect,
          backgroundColor: "rgba(255, 0, 0, 0.35)",
          borderRadius: 12,
          zIndex: 10,    // iOS hit order
          elevation: 5,  // Android hit order
        };

        return readOnly ? (
          <View key={i} pointerEvents="none" style={boxStyle} />
        ) : (
          <Pressable key={i} onPress={() => setSelected(f)} style={boxStyle} />
        );
      })}

      {showChangeStrip && !readOnly && (
        <View style={[styles.overlay, { zIndex: 5, elevation: 1 }]} pointerEvents="box-none">
          <Pressable onPress={onPress} style={{ paddingVertical: 8, paddingHorizontal: 16 }}>
            <Text style={styles.overlayText}>{busy ? "Busy…" : "Tap to change"}</Text>
          </Pressable>
        </View>
      )}

      {/* Modal */}
      {!readOnly && (
        <Modal
          visible={!!selected}
          transparent
          animationType="fade"
          onRequestClose={() => setSelected(null)}
        >
          <Pressable style={styles.backdrop} onPress={() => setSelected(null)}>
            <Pressable style={styles.sheet} onPress={(e) => e.stopPropagation()}>
              <Text style={{ fontSize: 16, marginBottom: 8 }}>
                Do you want to censor <Text style={{ fontWeight: "700" }}>{selected?.kind}</Text>?
              </Text>
              <Text style={{ marginBottom: 20, color: "#333" }}>{selected?.text}</Text>
              <View style={{ flexDirection: "row", gap: 12 }}>
                <Pressable style={[styles.btn, styles.btnGhost]} onPress={() => setSelected(null)}>
                  <Text style={styles.btnGhostText}>No</Text>
                </Pressable>
                <Pressable
                  style={[styles.btn, styles.btnPrimary]}
                  onPress={() => {
                    console.log("Censor:", selected);
                    setSelected(null);
                  }}
                >
                  <Text style={styles.btnPrimaryText}>Yes</Text>
                </Pressable>
              </View>
            </Pressable>
          </Pressable>
        </Modal>
      )}
    </View>
  );
}


const styles = StyleSheet.create({
  box: { flex: 1, width: "100%", borderRadius: 12, overflow: "hidden" },
  boxEmpty: {
    borderWidth: 2,
    borderStyle: "dashed",
    borderColor: "#BDBDBD",
    backgroundColor: "#FAFAFA",
    alignItems: "center",
    justifyContent: "center",
  },
  boxWithImage: { borderWidth: 0, backgroundColor: "#000" },
  boxInner: { alignItems: "center", gap: 6 },
  icon: { fontSize: 28, marginBottom: 4 },
  title: { fontSize: 16, fontWeight: "600" },
  subtitle: { fontSize: 12, color: "#666" },
  boxImage: { width: "100%", height: "100%" },
  overlay: {
    position: "absolute",
    bottom: 0,
    width: "100%",
    paddingVertical: 8,
    backgroundColor: "rgba(0,0,0,0.4)",
    alignItems: "center",
  },
  overlayText: { color: "#fff", fontWeight: "600" },
  uploadBtn: {
    backgroundColor: "#111",
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: "center",
  },
  uploadBtnText: { color: "#fff", fontWeight: "600" },
  backdrop: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
  },
  sheet: {
    width: "100%",
    maxWidth: 340,
    borderRadius: 12,
    backgroundColor: "white",
    padding: 20,
  },
  btn: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: "center",
  },
  btnGhost: { backgroundColor: "#e5e7eb" },
  btnGhostText: { color: "#111", fontWeight: "600" },
  btnPrimary: { backgroundColor: "#ef4444" },
  btnPrimaryText: { color: "white", fontWeight: "600" },
  fullscreenCenter: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
  },
});
