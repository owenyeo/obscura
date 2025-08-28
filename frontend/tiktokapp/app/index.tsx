// App.tsx
import { useState } from "react";
import { Image, View, Text, Pressable, StyleSheet, Platform } from "react-native";
import * as ImagePicker from "expo-image-picker";

function getBaseUrl() {
  return Platform.OS === "android" ? "http://10.0.2.2:8080" : "http://localhost:8080";
}

export default function App() {
  const [img, setImg] = useState<{ uri: string; type?: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

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
        // keep these to place boxes correctly with "contain"
        // (fallbacks in case some platforms miss them)
        w: a.width ?? 0,
        h: a.height ?? 0,
      } as any);
      setResult(null);
    }
  }

  async function upload() {
    if (!img) return;
    setBusy(true); setErr(null);
    try {
      const fd = new FormData();
      fd.append("file", {
        // @ts-ignore RN FormData file type
        uri: img.uri,
        name: "photo.jpg",
        type: img.type || "image/jpeg",
      });
      const r = await fetch(`${getBaseUrl()}/analyze/image`, {
        method: "POST",
        body: fd,
        headers: { "Content-Type": "multipart/form-data" },
      });
      if (!r.ok) throw new Error(`Upload failed: ${r.status}`);
      const json = await r.json();
      setResult(json);
    } catch (e: any) {
      setErr(String(e.message || e));
    } finally { setBusy(false); }
  }

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

function UploadBox({
  imageUri,
  result,
  onPress,
  busy,
}: {
  imageUri: string | null;
  result?: any;
  onPress: () => void;
  busy?: boolean;
}) {
  const [container, setContainer] = useState({ w: 0, h: 0 });
  const [natural, setNatural] = useState({ w: 0, h: 0 }); // intrinsic img size

  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      style={({ pressed }) => [
        styles.box,
        pressed && { opacity: 0.85 },
        imageUri ? styles.boxWithImage : styles.boxEmpty,
      ]}
    >
      {imageUri ? (
        <View
          style={{ flex: 1, position: "relative" }}
          onLayout={(e) => {
            const { width, height } = e.nativeEvent.layout;
            setContainer({ w: width, h: height });
          }}
        >
          <Image
            source={{ uri: imageUri }}
            style={styles.boxImage}
            resizeMode="contain"
            onLoad={(e) => {
              const { width, height } = (e.nativeEvent as any).source;
              setNatural({ w: width || natural.w, h: height || natural.h });
            }}
          />

          {/* Draw boxes using [x,y,w,h] normalized */}
          {result?.findings?.map((f: any, i: number) => {
            const [nx, ny, nw, nh] = f.bbox as number[];

            // compute displayed image rect within the container under "contain"
            const iw = natural.w || container.w;
            const ih = natural.h || container.h;
            const scale = Math.min(
              container.w / (iw || 1),
              container.h / (ih || 1)
            );
            const dispW = (iw || 0) * scale;
            const dispH = (ih || 0) * scale;
            const offsetX = (container.w - dispW) / 2;
            const offsetY = (container.h - dispH) / 2;

            // map normalized bbox to displayed pixels + offsets
            const left = offsetX + nx * dispW;
            const top = offsetY + ny * dispH;
            const width = nw * dispW;
            const height = nh * dispH;

            return (
              <View
                key={i}
                pointerEvents="none"
                style={{
                  position: "absolute",
                  left: left - 4,          // shift left edge
                  top: top - 4,            // shift top edge
                  width: width + 8,        // add horizontal padding
                  height: height + 8,      // add vertical padding
                  // borderWidth: 2,
                  // borderColor: "red",
                  backgroundColor: "rgba(255, 0, 0, 0.41)", // translucent fill
                  borderRadius: 12, // rounded corners
                }}
              >
                <View
                  style={{
                    position: "absolute",
                    left: 0,
                    top: -18,
                    backgroundColor: "rgba(255,255,255,0.85)",
                    paddingHorizontal: 4,
                  }}
                >
                  <Text style={{ fontSize: 10, color: "#c00" }}>
                    {f.kind}
                  </Text>
                </View>
              </View>
            );
          })}

          <View style={styles.overlay}>
            <Text style={styles.overlayText}>
              {busy ? "Busy…" : "Tap to change"}
            </Text>
          </View>
        </View>
      ) : (
        <View style={styles.boxInner}>
          <Text style={styles.icon}>⬆️</Text>
          <Text style={styles.title}>Tap to upload</Text>
          <Text style={styles.subtitle}>PNG or JPG, up to ~10MB</Text>
        </View>
      )}
    </Pressable>
  );
}


const styles = StyleSheet.create({
  box: { flex: 1, width: "100%", borderRadius: 12, overflow: "hidden" },
  boxEmpty: {
    borderWidth: 2, borderStyle: "dashed", borderColor: "#BDBDBD",
    backgroundColor: "#FAFAFA", alignItems: "center", justifyContent: "center",
  },
  boxWithImage: { borderWidth: 0, backgroundColor: "#000" },
  boxInner: { alignItems: "center", gap: 6 },
  icon: { fontSize: 28, marginBottom: 4 },
  title: { fontSize: 16, fontWeight: "600" },
  subtitle: { fontSize: 12, color: "#666" },
  boxImage: { width: "100%", height: "100%" },
  overlay: {
    position: "absolute", bottom: 0, width: "100%",
    paddingVertical: 8, backgroundColor: "rgba(0,0,0,0.4)", alignItems: "center",
  },
  overlayText: { color: "#fff", fontWeight: "600" },
  uploadBtn: { backgroundColor: "#111", paddingVertical: 12, borderRadius: 10, alignItems: "center" },
  uploadBtnText: { color: "#fff", fontWeight: "600" },
});
