import { Link } from 'react-router-dom'
import { ArrowRight, Shield, Zap, FileText, Users, Mic } from 'lucide-react'

export default function Home() {
  return (
    <div className="space-y-16">
      {/* Hero */}
      <section className="text-center py-16">
        <h1 className="text-4xl sm:text-5xl font-bold text-slate-900 mb-4">
          Mir Samozanyatykh
        </h1>
        <p className="text-lg text-slate-600 max-w-2xl mx-auto mb-8">
          Vse instrumenty dlya samozanyatykh v odnom meste: scheta, dogovory, klienty, 
          golosovoy assistent Svetlana i mnogoe drugoe.
        </p>
        <div className="flex justify-center gap-4">
          <Link to="/register" className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center gap-2">
            Nachat <ArrowRight className="w-4 h-4" />
          </Link>
          <Link to="/login" className="border border-slate-300 text-slate-700 px-6 py-3 rounded-lg font-medium hover:bg-slate-50 transition-colors">
            Vkhod
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <FeatureCard icon={FileText} title="Scheta i oplata" desc="Sozdavayte scheta, prinimayte oplatu cherez Yookassa, sledite za statusom." />
        <FeatureCard icon={Users} title="CRM" desc="Upravlyayte klientami i sdelkami. Vortonka prodazh, prioritety, sroki." />
        <FeatureCard icon={Shield} title="Dogovory" desc="GPH, IT-autsorsing, NDA — shablonny i s elektronoy podpisyyu." />
        <FeatureCard icon={Mic} title="Svetlana" desc="Golosovoy assistent na baze CosyVoice 3.0. Govorite — ona pomogaet." />
        <FeatureCard icon={Zap} title="Avtomatizatsiya" desc="Avtomaticheskaya generatsiya aktov, PDF, otchety." />
        <FeatureCard icon={Shield} title="Bezopasnost" desc="JWT s jti, CSRF, rate limiting, 2FA. OWASP-sovmestimo." />
      </section>
    </div>
  )
}

function FeatureCard({ icon: Icon, title, desc }: { icon: any, title: string, desc: string }) {
  return (
    <div className="bg-white p-6 rounded-xl border border-slate-200 hover:shadow-md transition-shadow">
      <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center mb-4">
        <Icon className="w-5 h-5 text-blue-600" />
      </div>
      <h3 className="font-semibold text-slate-800 mb-2">{title}</h3>
      <p className="text-sm text-slate-600">{desc}</p>
    </div>
  )
}
