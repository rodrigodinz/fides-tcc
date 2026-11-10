import { useState } from "react";
import { urlImagem } from "../api/config.js";
import simbolo from "../assets/simbolo-fides.svg";

/**
 * Retrato vindo de foto_url (caminho relativo da API, prefixado pela origem).
 * Sem foto ou com 404: fundo pergaminho com o símbolo, sem imagem inventada.
 * Proporção fixa 4:5 (e width/height) para não haver deslocamento de layout.
 */
export default function RetratoSanto({ fotoUrl, nome, decorativo = false, className = "", carregamento = "lazy" }) {
  const src = urlImagem(fotoUrl);
  const [falhou, setFalhou] = useState(false);
  const mostrar = src && !falhou;
  return (
    <div className={`fd-retrato ${className}`.trim()}>
      {mostrar ? (
        <img src={src} alt={decorativo ? "" : `Retrato de ${nome}`} width="400" height="500" loading={carregamento} decoding="async" onError={() => setFalhou(true)} />
      ) : (
        <div className="fd-retrato__vazio" role={decorativo ? undefined : "img"} aria-label={decorativo ? undefined : `Retrato de ${nome} não disponível`}>
          <img src={simbolo} alt="" width="44" height="57" />
          <span aria-hidden="true">Retrato não disponível</span>
        </div>
      )}
    </div>
  );
}
