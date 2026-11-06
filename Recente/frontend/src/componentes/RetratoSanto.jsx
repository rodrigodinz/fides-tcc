import { useState } from "react";
import { montarUrlDaImagem } from "../api/config.js";
import simboloDoFides from "../assets/simbolo-fides.svg";

// foto do santo; se a imagem faltar ou falhar, mostra o símbolo do Fides
export default function RetratoSanto({ fotoUrl, nome, decorativo = false, className = "", carregamento = "lazy" }) {
  const urlDaImagem = montarUrlDaImagem(fotoUrl);
  const [imagemFalhou, setImagemFalhou] = useState(false);
  const mostrarImagem = urlDaImagem && !imagemFalhou;
  return (
    <div className={`fd-retrato ${className}`.trim()}>
      {mostrarImagem ? (
        // onError: se a imagem não carregar, troca pelo símbolo
        <img src={urlDaImagem} alt={decorativo ? "" : `Retrato de ${nome}`} width="400" height="500" loading={carregamento} decoding="async" onError={() => setImagemFalhou(true)} />
      ) : (
        <div className="fd-retrato__vazio" role={decorativo ? undefined : "img"} aria-label={decorativo ? undefined : `Retrato de ${nome} não disponível`}>
          <img src={simboloDoFides} alt="" width="44" height="57" />
          <span aria-hidden="true">Retrato não disponível</span>
        </div>
      )}
    </div>
  );
}
